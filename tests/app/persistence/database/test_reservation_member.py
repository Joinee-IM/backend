from app.base import do
from app.persistence.database import reservation_member
from tests import AsyncMock, AsyncTestCase, Mock, patch


class TestBatchAdd(AsyncTestCase):
    def setUp(self) -> None:
        self.reservation_id = 1
        self.member_ids = [1, 2]
        self.params = {'account_id_0': 1, 'account_id_1': 2, 'is_manager_0': False, 'is_manager_1': False}

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', new_callable=AsyncMock)
    async def test_happy_path(self, mock_execute: AsyncMock, mock_init: Mock):
        mock_execute.return_value = None

        result = await reservation_member.batch_add(
            reservation_id=self.reservation_id,
            member_ids=self.member_ids,
        )

        self.assertIsNone(result)

        mock_init.assert_called_with(
            sql=r'INSERT INTO reservation_member'
                r'            (reservation_id, account_id, is_manager, is_joined)'
                r'     VALUES (%(reservation_id)s, %(account_id_0)s, %(is_manager_0)s, %(is_joined)s),'
                r' (%(reservation_id)s, %(account_id_1)s, %(is_manager_1)s, %(is_joined)s)',
            reservation_id=self.reservation_id, is_joined=False, **self.params,
        )


class TestBrowse(AsyncTestCase):
    def setUp(self) -> None:
        self.reservation_id = 1
        self.account_id = 1
        self.params = {
            'account_id': self.account_id,
            'reservation_id': self.reservation_id,
        }
        self.raw_reservation_members = [
            (1, 1, True, True),
        ]
        self.reservation_members = [
            do.ReservationMember(
                reservation_id=1,
                account_id=1,
                is_manager=True,
                is_joined=True,
            )
        ]

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_all', new_callable=AsyncMock)
    async def test_happy_path(self, mock_fetch: AsyncMock, mock_init: Mock):
        mock_fetch.return_value = self.raw_reservation_members

        result = await reservation_member.browse(
            account_id=self.account_id,
            reservation_id=self.reservation_id,
        )

        self.assertEqual(result, self.reservation_members)
        mock_init.assert_called_with(
            sql=r'SELECT reservation_id, account_id, is_manager, is_joined'
                r'  FROM reservation_member'
                fr' WHERE reservation_id = %(reservation_id)s'
                fr' AND account_id = %(account_id)s'
                r' ORDER BY is_manager, account_id',
            **self.params,
        )
