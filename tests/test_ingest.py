import unittest
from lega.ingest import main  # , _work
# from lega.utils.exceptions import NotFoundInInbox
from unittest import mock
# from testfixtures import tempdir
# from pathlib import PosixPath
# from . import pgp_data


class testIngest(unittest.TestCase):
    """Ingest.

    Testing ingestion functionalities.
    """

    @mock.patch('lega.ingest.get_connection')
    @mock.patch('lega.ingest.consume')
    def test_main(self, mock_consume, mock_connection):
        """Test main verify, by mocking cosume call."""
        mock_consume.return_value = mock.MagicMock()
        main()
        mock_consume.assert_called()

    # @tempdir()
    # @mock.patch('lega.ingest.get_header')
    # @mock.patch('lega.ingest.Path')
    # @mock.patch('lega.ingest.db')
    # def test_work(self, mock_db, mock_path, mock_header, filedir):
    #     """Test ingest worker, should send a messge."""
    #     # Mocking a lot of stuff, ast it is previously tested
    #     mock_path = mock.Mock(spec=PosixPath)
    #     mock_path.return_value = ''
    #     mock_header.return_value = b'beginning', b'header'
    #     mock_db.insert_file.return_value = 'db_file_id'
    #     mock_db.set_status.return_value = 'db_status'
    #     mock_db.Status = mock.MagicMock(name='Archived')
    #     mock_db.Status.Archived.value = 'Archived'
    #     store = mock.MagicMock()
    #     store.location.return_value = 'smth'
    #     store.open.return_value = mock.MagicMock()
    #     mock_broker = mock.MagicMock(name='channel')
    #     mock_broker.channel.return_value = mock.Mock()
    #     infile = filedir.write('infile.in', bytearray.fromhex(pgp_data.ENC_FILE))
    #     data = {'filepath': infile, 'stable_id': 1, 'user': 'user_id@exlir-europe.org'}
    #     result = _work(store, mock_broker, data)
    #     mocked = {'filepath': infile, 'stable_id': 1,
    #               'user': 'user_id@exlir-europe.org', 'file_id': 'db_file_id', 'user_id': 'user_id',
    #               'org_msg': {'filepath': infile, 'stable_id': 1, 'user': 'user_id@exlir-europe.org'},
    #               'status': 'Archived', 'header': '626567696e6e696e67686561646572',
    #               'vault_path': 'smth', 'vault_type': 'MagicMock'}
    #     self.assertEqual(mocked, result)
    #     filedir.cleanup()
