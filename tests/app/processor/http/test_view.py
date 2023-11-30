from datetime import datetime

import app.exceptions as exc
from app.base import do, enums, vo
from app.processor.http import view
from app.utils import Response
from app.utils.security import AuthedAccount
from tests import AsyncMock, AsyncTestCase, MockContext, patch


class TestViewMyReservation(AsyncTestCase):
    def setUp(self) -> None:
        self.params = view.ViewMyReservationParams(
            account_id=1,
            sort_by=enums.ViewMyReservationSortBy.time,
            order=enums.Sorter.desc,
            limit=1,
            offset=0,
        )
        self.total_count = 1
        self.context = {'AUTHED_ACCOUNT': AuthedAccount(id=1, time=datetime(2023, 11, 4))}
        self.wrong_context = {'AUTHED_ACCOUNT': AuthedAccount(id=2, time=datetime(2023, 11, 4))}

        self.reservations = [
            vo.ViewMyReservation(
                reservation_id=1,
                start_time=datetime(2023, 11, 11),
                end_time=datetime(2023, 11, 17),
                stadium_name='stadium_name',
                venue_name='venue_name',
                is_manager=True,
                vacancy=1,
                status=enums.ReservationStatus.finished,
            ),
        ]
        self.expect_result = Response(data=view.ViewMyReservationOutput(
            data=self.reservations,
            total_count=self.total_count,
            limit=self.params.limit,
            offset=self.params.offset,
        ))

    @patch('app.processor.http.view.context', new_callable=MockContext)
    @patch('app.persistence.database.view.browse_my_reservation', new_callable=AsyncMock)
    async def test_happy_path(self, mock_browse: AsyncMock, mock_context: MockContext):
        mock_context._context = self.context
        mock_browse.return_value = self.reservations, self.total_count

        result = await view.view_my_reservation(params=self.params)

        self.assertEqual(result, self.expect_result)
        mock_browse.assert_called_with(
            account_id=self.params.account_id,
            sort_by=self.params.sort_by,
            order=self.params.order,
            limit=self.params.limit,
            offset=self.params.offset,
        )

        mock_context.reset_context()

    @patch('app.processor.http.view.context', new_callable=MockContext)
    async def test_no_permission(self, mock_context: MockContext):
        mock_context._context = self.wrong_context

        with self.assertRaises(exc.NoPermission):
            await view.view_my_reservation(params=self.params)

        mock_context.reset_context()


class TestViewProviderStadium(AsyncTestCase):
    def setUp(self) -> None:
        self.account_id = 1
        self.context = {'AUTHED_ACCOUNT': AuthedAccount(id=self.account_id, time=datetime(2023, 11, 4))}
        self.normal_account = do.Account(
            id=1, email='email@email.com', nickname='nickname', gender=enums.GenderType.male, image_uuid=None,
            role=enums.RoleType.normal, is_verified=True, is_google_login=False,
        )
        self.provider_account = do.Account(
            id=1, email='email@email.com', nickname='nickname', gender=enums.GenderType.male, image_uuid=None,
            role=enums.RoleType.provider, is_verified=True, is_google_login=False,
        )
        self.params = view.ViewProviderStadiumParams(
            city_id=1,
            district_id=1,
            is_published=True,
            sort_by=enums.ViewProviderStadiumSortBy.stadium_name,
            order=enums.Sorter.desc,
            limit=1,
            offset=0,
        )
        self.stadiums = [
            vo.ViewProviderStadium(
                stadium_id=1,
                city_name='city',
                district_name='district',
                stadium_name='stadium',
                venue_count=0,
                is_published=True,
            ),
        ]
        self.total_count = 1
        self.expect_result = Response(data=view.ViewProviderStadiumOutput(
            data=self.stadiums,
            total_count=self.total_count,
            limit=self.params.limit,
            offset=self.params.offset,
        ))

    @patch('app.processor.http.view.context', new_callable=MockContext)
    @patch('app.persistence.database.account.read', new_callable=AsyncMock)
    @patch('app.persistence.database.view.browse_provider_stadium', new_callable=AsyncMock)
    async def test_happy_path(self, mock_browse: AsyncMock, mock_read: AsyncMock, mock_context: MockContext):
        mock_context._context = self.context
        mock_read.return_value = self.provider_account
        mock_browse.return_value = self.stadiums, self.total_count

        result = await view.view_provider_stadium(params=self.params)

        self.assertEqual(result, self.expect_result)
        mock_read.assert_called_with(
            account_id=self.account_id,
        )
        mock_browse.assert_called_with(
            owner_id=self.provider_account.id,
            city_id=self.params.city_id,
            district_id=self.params.district_id,
            is_published=self.params.is_published,
            sort_by=self.params.sort_by,
            order=self.params.order,
            limit=self.params.limit,
            offset=self.params.offset,
        )

        mock_context.reset_context()

    @patch('app.processor.http.view.context', new_callable=MockContext)
    @patch('app.persistence.database.account.read', new_callable=AsyncMock)
    @patch('app.persistence.database.view.browse_provider_stadium', new_callable=AsyncMock)
    async def test_no_permission(self, mock_browse: AsyncMock, mock_read: AsyncMock, mock_context: MockContext):
        mock_context._context = self.context
        mock_read.return_value = self.normal_account
        mock_browse.return_value = self.stadiums, self.total_count

        with self.assertRaises(exc.NoPermission):
            await view.view_provider_stadium(params=self.params)

        mock_read.assert_called_with(
            account_id=self.account_id,
        )
        mock_browse.assert_not_called()

        mock_context.reset_context()


class TestViewProviderVenue(AsyncTestCase):
    def setUp(self) -> None:
        self.account_id = 1
        self.context = {'AUTHED_ACCOUNT': AuthedAccount(id=self.account_id, time=datetime(2023, 11, 4))}
        self.normal_account = do.Account(
            id=1, email='email@email.com', nickname='nickname', gender=enums.GenderType.male, image_uuid=None,
            role=enums.RoleType.normal, is_verified=True, is_google_login=False,
        )
        self.provider_account = do.Account(
            id=1, email='email@email.com', nickname='nickname', gender=enums.GenderType.male, image_uuid=None,
            role=enums.RoleType.provider, is_verified=True, is_google_login=False,
        )
        self.params = view.ViewProviderVenueParams(
            stadium_id=1,
            is_published=True,
            sort_by=enums.ViewProviderVenueSortBy.stadium_name,
            order=enums.Sorter.asc,
            limit=10,
            offset=0,
        )
        self.total_count = 1
        self.venues = [
            vo.ViewProviderVenue(
                venue_id=1,
                stadium_name='s1',
                venue_name='v1',
                court_count=1,
                area=1,
                is_published=True,
            ),
            vo.ViewProviderVenue(
                venue_id=2,
                stadium_name='s2',
                venue_name='v2',
                court_count=2,
                area=2,
                is_published=True,
            ),
        ]
        self.expect_result = Response(data=view.ViewProviderVenueOutput(
            data=self.venues,
            total_count=self.total_count,
            limit=self.params.limit,
            offset=self.params.offset,
        ))

    @patch('app.processor.http.view.context', new_callable=MockContext)
    @patch('app.persistence.database.account.read', new_callable=AsyncMock)
    @patch('app.persistence.database.view.browse_provider_venue', new_callable=AsyncMock)
    async def test_happy_path(self, mock_browse: AsyncMock, mock_read: AsyncMock, mock_context: MockContext):
        mock_context._context = self.context
        mock_read.return_value = self.provider_account
        mock_browse.return_value = self.venues, self.total_count

        result = await view.view_provider_venue(
            params=self.params,
        )

        self.assertEqual(result, self.expect_result)

    @patch('app.processor.http.view.context', new_callable=MockContext)
    @patch('app.persistence.database.account.read', new_callable=AsyncMock)
    @patch('app.persistence.database.view.browse_provider_venue', new_callable=AsyncMock)
    async def test_no_permission(self, mock_browse: AsyncMock, mock_read: AsyncMock, mock_context: MockContext):
        mock_context._context = self.context
        mock_read.return_value = self.normal_account
        mock_browse.return_value = self.venues, self.total_count

        with self.assertRaises(exc.NoPermission):
            await view.view_provider_venue(
                params=self.params,
            )

        mock_context.reset_context()


class TestViewProviderCourt(AsyncTestCase):
    def setUp(self) -> None:
        self.account_id = 1
        self.context = {'AUTHED_ACCOUNT': AuthedAccount(id=self.account_id, time=datetime(2023, 11, 4))}
        self.normal_account = do.Account(
            id=1, email='email@email.com', nickname='nickname', gender=enums.GenderType.male, image_uuid=None,
            role=enums.RoleType.normal, is_verified=True, is_google_login=False,
        )
        self.provider_account = do.Account(
            id=1, email='email@email.com', nickname='nickname', gender=enums.GenderType.male, image_uuid=None,
            role=enums.RoleType.provider, is_verified=True, is_google_login=False,
        )
        self.params = view.ViewProviderCourtParams(
            stadium_id=1,
            venue_id=1,
            is_published=True,
            sort_by=enums.ViewProviderCourtSortBy.stadium_name,
            order=enums.Sorter.desc,
            limit=10,
            offset=0,
        )
        self.total_count = 1
        self.courts = [
            vo.ViewProviderCourt(
                court_id=1,
                stadium_name='s1',
                venue_name='v1',
                court_number=1,
                is_published=True,
            ),
            vo.ViewProviderCourt(
                court_id=2,
                stadium_name='s2',
                venue_name='v2',
                court_number=2,
                is_published=False,
            ),
        ]
        self.expect_result = Response(data=view.ViewProviderCourtOutput(
            data=self.courts,
            total_count=self.total_count,
            limit=self.params.limit,
            offset=self.params.offset,
        ))

    @patch('app.processor.http.view.context', new_callable=MockContext)
    @patch('app.persistence.database.account.read', new_callable=AsyncMock)
    @patch('app.persistence.database.view.browse_provider_court', new_callable=AsyncMock)
    async def test_happy_path(self, mock_browse: AsyncMock, mock_read: AsyncMock, mock_context: MockContext):
        mock_context._context = self.context
        mock_read.return_value = self.provider_account
        mock_browse.return_value = self.courts, self.total_count

        result = await view.view_provider_court(
            params=self.params,
        )
        self.assertEqual(result, self.expect_result)
        mock_context.reset_context()

    @patch('app.processor.http.view.context', new_callable=MockContext)
    @patch('app.persistence.database.account.read', new_callable=AsyncMock)
    @patch('app.persistence.database.view.browse_provider_court', new_callable=AsyncMock)
    async def test_no_permission(self, mock_browse: AsyncMock, mock_read: AsyncMock, mock_context: MockContext):
        mock_context._context = self.context
        mock_read.return_value = self.normal_account
        mock_browse.return_value = self.courts, self.total_count

        with self.assertRaises(exc.NoPermission):
            await view.view_provider_court(
                params=self.params,
            )
        mock_browse.assert_not_called()
        mock_context.reset_context()
