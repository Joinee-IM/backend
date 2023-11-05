from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Type, Union

import fastapi.openapi.utils


def get_openapi_path(
    *,
    route: fastapi.openapi.utils.routing.APIRoute,
    operation_ids: Set[str],
    schema_generator: fastapi.openapi.utils.GenerateJsonSchema,
    model_name_map: fastapi.openapi.utils.ModelNameMap,
    field_mapping: Dict[
        Tuple[fastapi.openapi.utils.ModelField, fastapi.openapi.utils.Literal['validation', 'serialization']],
        fastapi.openapi.utils.JsonSchemaValue
    ],
    separate_input_output_schemas: bool = True,
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    path = {}
    security_schemes: Dict[str, Any] = {}
    definitions: Dict[str, Any] = {}
    assert route.methods is not None, 'Methods must be a list'
    if isinstance(route.response_class, fastapi.openapi.utils.DefaultPlaceholder):
        current_response_class: Type[fastapi.openapi.utils.Response] = route.response_class.value
    else:
        current_response_class = route.response_class
    assert current_response_class, 'A response class is needed to generate OpenAPI'
    route_response_media_type: Optional[str] = current_response_class.media_type
    if route.include_in_schema:
        for method in route.methods:
            operation = fastapi.openapi.utils.get_openapi_operation_metadata(
                route=route, method=method, operation_ids=operation_ids
            )
            parameters: List[Dict[str, Any]] = []
            flat_dependant = fastapi.openapi.utils.get_flat_dependant(route.dependant, skip_repeats=True)
            security_definitions, operation_security = fastapi.openapi.utils.get_openapi_security_definitions(
                flat_dependant=flat_dependant
            )
            if operation_security:
                operation.setdefault('security', []).extend(operation_security)
            if security_definitions:
                security_schemes.update(security_definitions)
            all_route_params = fastapi.openapi.utils.get_flat_params(route.dependant)
            operation_parameters = fastapi.openapi.utils.get_openapi_operation_parameters(
                all_route_params=all_route_params,
                schema_generator=schema_generator,
                model_name_map=model_name_map,
                field_mapping=field_mapping,
                separate_input_output_schemas=separate_input_output_schemas,
            )
            parameters.extend(operation_parameters)
            if parameters:
                all_parameters = {
                    (param['in'], param['name']): param for param in parameters
                }
                required_parameters = {
                    (param['in'], param['name']): param
                    for param in parameters
                    if param.get('required')
                }
                # Make sure required definitions of the same parameter take precedence
                # over non-required definitions
                all_parameters.update(required_parameters)
                operation['parameters'] = list(all_parameters.values())
            if method in fastapi.openapi.utils.METHODS_WITH_BODY:
                request_body_oai = fastapi.openapi.utils.get_openapi_operation_request_body(
                    body_field=route.body_field,
                    schema_generator=schema_generator,
                    model_name_map=model_name_map,
                    field_mapping=field_mapping,
                    separate_input_output_schemas=separate_input_output_schemas,
                )
                if request_body_oai:
                    operation['requestBody'] = request_body_oai
            if route.callbacks:
                callbacks = {}
                for callback in route.callbacks:
                    if isinstance(callback, fastapi.openapi.utils.routing.APIRoute):
                        (
                            cb_path,
                            cb_security_schemes,
                            cb_definitions,
                        ) = get_openapi_path(
                            route=callback,
                            operation_ids=operation_ids,
                            schema_generator=schema_generator,
                            model_name_map=model_name_map,
                            field_mapping=field_mapping,
                            separate_input_output_schemas=separate_input_output_schemas,
                        )
                        callbacks[callback.name] = {callback.path: cb_path}
                operation['callbacks'] = callbacks
            status_code = None
            if route.status_code is not None:
                status_code = str(route.status_code)
            else:
                # It would probably make more sense for all response classes to have an
                # explicit default status_code, and to extract it from them, instead of
                # doing this inspection tricks, that would probably be in the future
                # TODO: probably make status_code a default class attribute for all
                # responses in Starlette
                response_signature = fastapi.openapi.utils.inspect.signature(current_response_class.__init__)
                status_code_param = response_signature.parameters.get('status_code')
                if status_code_param is not None:
                    if isinstance(status_code_param.default, int):
                        status_code = str(status_code_param.default)
            operation.setdefault('responses', {}).setdefault(status_code, {})[
                "description"
            ] = route.response_description
            if route_response_media_type and fastapi.openapi.utils.is_body_allowed_for_status_code(
                route.status_code
            ):
                response_schema = {"type": "string"}
                if fastapi.openapi.utils.lenient_issubclass(current_response_class, fastapi.openapi.utils.JSONResponse):
                    if route.response_field:
                        response_schema = fastapi.openapi.utils.get_schema_from_model_field(
                            field=route.response_field,
                            schema_generator=schema_generator,
                            model_name_map=model_name_map,
                            field_mapping=field_mapping,
                            separate_input_output_schemas=separate_input_output_schemas,
                        )
                    else:
                        response_schema = {}
                operation.setdefault("responses", {}).setdefault(
                    status_code, {}
                ).setdefault("content", {}).setdefault(route_response_media_type, {})[
                    "schema"
                ] = response_schema
            if route.responses:
                operation_responses = operation.setdefault("responses", {})
                for (
                    additional_status_code,
                    additional_response,
                ) in route.responses.items():
                    process_response = additional_response.copy()
                    process_response.pop("model", None)
                    status_code_key = str(additional_status_code).upper()
                    if status_code_key == "DEFAULT":
                        status_code_key = "default"
                    openapi_response = operation_responses.setdefault(
                        status_code_key, {}
                    )
                    assert isinstance(
                        process_response, dict
                    ), "An additional response must be a dict"
                    field = route.response_fields.get(additional_status_code)
                    if field:
                        additional_field_schema = fastapi.openapi.utils.get_schema_from_model_field(
                            field=field,
                            schema_generator=schema_generator,
                            model_name_map=model_name_map,
                            field_mapping=field_mapping,
                            separate_input_output_schemas=separate_input_output_schemas,
                        )
                        media_type = route_response_media_type or "application/json"
                        additional_schema = (
                            process_response.setdefault("content", {})
                            .setdefault(media_type, {})
                            .setdefault("schema", {})
                        )
                        fastapi.openapi.utils.deep_dict_update(additional_schema, additional_field_schema)
                    status_text: Optional[str] = fastapi.openapi.utils.status_code_ranges.get(
                        str(additional_status_code).upper()
                    ) or fastapi.openapi.utils.http.client.responses.get(int(additional_status_code))
                    description = (
                        process_response.get("description")
                        or openapi_response.get("description")
                        or status_text
                        or "Additional Response"
                    )
                    fastapi.openapi.utils.deep_dict_update(openapi_response, process_response)
                    openapi_response["description"] = description
            # http422 = str(fastapi.openapi.utils.HTTP_422_UNPROCESSABLE_ENTITY)
            # if (all_route_params or route.body_field) and not any(
            #     status in operation["responses"]
            #     for status in [http422, "4XX", "default"]
            # ):
            #     operation["responses"][http422] = {
            #         "description": "Validation Error",
            #         "content": {
            #             "application/json": {
            #                 "schema": {"$ref": fastapi.openapi.utils.REF_PREFIX + "HTTPValidationError"}
            #             }
            #         },
            #     }
            #     if "ValidationError" not in definitions:
            #         definitions.update(
            #             {
            #                 "ValidationError": fastapi.openapi.utils.validation_error_definition,
            #                 "HTTPValidationError": fastapi.openapi.utils.validation_error_response_definition,
            #             }
            #         )
            if route.openapi_extra:
                fastapi.openapi.utils.deep_dict_update(operation, route.openapi_extra)
            path[method.lower()] = operation
    return path, security_schemes, definitions


def get_openapi(
    *,
    title: str,
    version: str,
    openapi_version: str = "3.1.0",
    summary: Optional[str] = None,
    description: Optional[str] = None,
    routes: Sequence[fastapi.openapi.utils.BaseRoute],
    webhooks: Optional[Sequence[fastapi.openapi.utils.BaseRoute]] = None,
    tags: Optional[List[Dict[str, Any]]] = None,
    servers: Optional[List[Dict[str, Union[str, Any]]]] = None,
    terms_of_service: Optional[str] = None,
    contact: Optional[Dict[str, Union[str, Any]]] = None,
    license_info: Optional[Dict[str, Union[str, Any]]] = None,
    separate_input_output_schemas: bool = True,
) -> Dict[str, Any]:
    info: Dict[str, Any] = {"title": title, "version": version}
    if summary:
        info["summary"] = summary
    if description:
        info["description"] = description
    if terms_of_service:
        info["termsOfService"] = terms_of_service
    if contact:
        info["contact"] = contact
    if license_info:
        info["license"] = license_info
    output: Dict[str, Any] = {"openapi": openapi_version, "info": info}
    if servers:
        output["servers"] = servers
    components: Dict[str, Dict[str, Any]] = {}
    paths: Dict[str, Dict[str, Any]] = {}
    webhook_paths: Dict[str, Dict[str, Any]] = {}
    operation_ids: Set[str] = set()
    all_fields = fastapi.openapi.utils.get_fields_from_routes(list(routes or []) + list(webhooks or []))
    model_name_map = fastapi.openapi.utils.get_compat_model_name_map(all_fields)
    schema_generator = fastapi.openapi.utils.GenerateJsonSchema(ref_template=fastapi.openapi.utils.REF_TEMPLATE)
    field_mapping, definitions = fastapi.openapi.utils.get_definitions(
        fields=all_fields,
        schema_generator=schema_generator,
        model_name_map=model_name_map,
        separate_input_output_schemas=separate_input_output_schemas,
    )
    for route in routes or []:
        if isinstance(route, fastapi.openapi.utils.routing.APIRoute):
            result = get_openapi_path(
                route=route,
                operation_ids=operation_ids,
                schema_generator=schema_generator,
                model_name_map=model_name_map,
                field_mapping=field_mapping,
                separate_input_output_schemas=separate_input_output_schemas,
            )
            if result:
                path, security_schemes, path_definitions = result
                if path:
                    paths.setdefault(route.path_format, {}).update(path)
                if security_schemes:
                    components.setdefault("securitySchemes", {}).update(
                        security_schemes
                    )
                if path_definitions:
                    definitions.update(path_definitions)
    for webhook in webhooks or []:
        if isinstance(webhook, fastapi.openapi.utils.routing.APIRoute):
            result = get_openapi_path(
                route=webhook,
                operation_ids=operation_ids,
                schema_generator=schema_generator,
                model_name_map=model_name_map,
                field_mapping=field_mapping,
                separate_input_output_schemas=separate_input_output_schemas,
            )
            if result:
                path, security_schemes, path_definitions = result
                if path:
                    webhook_paths.setdefault(webhook.path_format, {}).update(path)
                if security_schemes:
                    components.setdefault("securitySchemes", {}).update(
                        security_schemes
                    )
                if path_definitions:
                    definitions.update(path_definitions)
    if definitions:
        components["schemas"] = {k: definitions[k] for k in sorted(definitions)}
    if components:
        output["components"] = components
    output["paths"] = paths
    if webhook_paths:
        output["webhooks"] = webhook_paths
    if tags:
        output["tags"] = tags
    return fastapi.openapi.utils.jsonable_encoder(fastapi.openapi.utils.OpenAPI(**output),
                                                  by_alias=True,
                                                  exclude_none=True)


class FastAPI(fastapi.FastAPI):
    def openapi(self) -> Dict[str, Any]:
        if not self.openapi_schema:
            self.openapi_schema = get_openapi(
                title=self.title,
                version=self.version,
                openapi_version=self.openapi_version,
                summary=self.summary,
                description=self.description,
                terms_of_service=self.terms_of_service,
                contact=self.contact,
                license_info=self.license_info,
                routes=self.routes,
                webhooks=self.webhooks.routes,
                tags=self.openapi_tags,
                servers=self.servers,
                separate_input_output_schemas=self.separate_input_output_schemas,
            )
        return self.openapi_schema
        return self.openapi_schema
