import unittest
from unittest.mock import patch, mock_open
import app_fika

class TestGuardarBD(unittest.TestCase):
    @patch('app_fika.json.dump')
    @patch('builtins.open', new_callable=mock_open)
    def test_guardar_bd_success(self, mock_file, mock_json_dump):
        """Test that guardar_bd correctly opens the file and dumps JSON."""
        datos = {"clave": "valor", "numero": 123}
        app_fika.guardar_bd(datos)

        mock_file.assert_called_once_with(app_fika.ARCHIVO_BD, "w")
        mock_json_dump.assert_called_once_with(datos, mock_file(), indent=4)

    @patch('builtins.open', side_effect=PermissionError("Permission denied"))
    def test_guardar_bd_permission_error(self, mock_file):
        """Test that guardar_bd propagates IOError if the file cannot be opened."""
        datos = {"clave": "valor"}
        with self.assertRaises(PermissionError):
            app_fika.guardar_bd(datos)

    @patch('app_fika.json.dump', side_effect=TypeError("Object of type set is not JSON serializable"))
    @patch('builtins.open', new_callable=mock_open)
    def test_guardar_bd_json_error(self, mock_file, mock_json_dump):
        """Test that guardar_bd propagates TypeError if JSON dumping fails."""
        datos = {"clave": set([1, 2, 3])}
        with self.assertRaises(TypeError):
            app_fika.guardar_bd(datos)

if __name__ == '__main__':
    unittest.main()
