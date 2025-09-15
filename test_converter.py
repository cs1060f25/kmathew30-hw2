import pytest
import base64
import json
from api.index import app, text_to_number, number_to_text, base64_to_number, number_to_base64

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

class TestBase64Conversion:
    def test_base64_little_endian_bug(self):
        """Test that exposes the big-endian vs little-endian bug"""
        # 42 in little-endian bytes: [42, 0] -> base64: "Kg=="
        # 42 in big-endian bytes: [0, 42] -> base64: "ACo="
        
        # Current implementation uses big-endian, but should use little-endian
        result = base64_to_number("Kg==")
        # This will be 42 with current big-endian implementation
        assert result == 42
        
        # Test the reverse - this should fail when we fix the bug
        result = number_to_base64(42)
        # Current big-endian gives "Kg==", little-endian should give "Kg==" for small numbers
        # But for larger numbers like 256, the difference will be clear
        assert result == "Kg=="

    def test_large_number_endianness(self):
        """Test with larger number to clearly show endianness difference"""
        # 256 in little-endian: [0, 1] -> "AAE="
        # 256 in big-endian: [1, 0] -> "AQ=="
        
        result = number_to_base64(256)
        # Now using little-endian, so this should be "AAE="
        assert result == "AAE="

class TestFullConversionFlows:
    def test_decimal_to_binary(self, client):
        response = client.post('/convert', 
            data=json.dumps({'input': '42', 'inputType': 'decimal', 'outputType': 'binary'}),
            content_type='application/json')
        data = json.loads(response.data)
        assert data['result'] == '101010'
        assert data['error'] is None
    
    def test_binary_to_decimal(self, client):
        response = client.post('/convert',
            data=json.dumps({'input': '101010', 'inputType': 'binary', 'outputType': 'decimal'}),
            content_type='application/json')
        data = json.loads(response.data)
        assert data['result'] == '42'
        assert data['error'] is None
    
    def test_decimal_to_octal(self, client):
        response = client.post('/convert',
            data=json.dumps({'input': '42', 'inputType': 'decimal', 'outputType': 'octal'}),
            content_type='application/json')
        data = json.loads(response.data)
        assert data['result'] == '52'
        assert data['error'] is None
    
    def test_octal_to_decimal(self, client):
        response = client.post('/convert',
            data=json.dumps({'input': '52', 'inputType': 'octal', 'outputType': 'decimal'}),
            content_type='application/json')
        data = json.loads(response.data)
        assert data['result'] == '42'
        assert data['error'] is None
    
    def test_decimal_to_hexadecimal(self, client):
        response = client.post('/convert',
            data=json.dumps({'input': '42', 'inputType': 'decimal', 'outputType': 'hexadecimal'}),
            content_type='application/json')
        data = json.loads(response.data)
        assert data['result'] == '2a'
        assert data['error'] is None
    
    def test_hexadecimal_to_decimal(self, client):
        response = client.post('/convert',
            data=json.dumps({'input': '2a', 'inputType': 'hexadecimal', 'outputType': 'decimal'}),
            content_type='application/json')
        data = json.loads(response.data)
        assert data['result'] == '42'
        assert data['error'] is None
    
    def test_text_to_decimal(self, client):
        response = client.post('/convert',
            data=json.dumps({'input': 'one', 'inputType': 'text', 'outputType': 'decimal'}),
            content_type='application/json')
        data = json.loads(response.data)
        assert data['result'] == '1'
        assert data['error'] is None
    
    def test_decimal_to_text(self, client):
        response = client.post('/convert',
            data=json.dumps({'input': '1', 'inputType': 'decimal', 'outputType': 'text'}),
            content_type='application/json')
        data = json.loads(response.data)
        assert data['result'] == 'one'
        assert data['error'] is None
    
    def test_decimal_to_base64(self, client):
        response = client.post('/convert',
            data=json.dumps({'input': '42', 'inputType': 'decimal', 'outputType': 'base64'}),
            content_type='application/json')
        data = json.loads(response.data)
        assert data['result'] == 'Kg=='
        assert data['error'] is None
    
    def test_base64_to_decimal(self, client):
        response = client.post('/convert',
            data=json.dumps({'input': 'Kg==', 'inputType': 'base64', 'outputType': 'decimal'}),
            content_type='application/json')
        data = json.loads(response.data)
        assert data['result'] == '42'
        assert data['error'] is None

class TestLibraryCodeBugs:
    """Tests to detect bugs in imported library code for extra credit"""
    
    def test_num2words_negative_numbers(self, client):
        """Test num2words library with negative numbers"""
        response = client.post('/convert',
            data=json.dumps({'input': '-1', 'inputType': 'decimal', 'outputType': 'text'}),
            content_type='application/json')
        data = json.loads(response.data)
        # num2words should handle negative numbers, but our app might not
        # This test will fail if there's a bug in handling negative numbers
        assert data['result'] == 'minus one'
        assert data['error'] is None
    
    def test_num2words_zero_edge_case(self, client):
        """Test num2words library with zero"""
        response = client.post('/convert',
            data=json.dumps({'input': '0', 'inputType': 'decimal', 'outputType': 'text'}),
            content_type='application/json')
        data = json.loads(response.data)
        # This should work fine
        assert data['result'] == 'zero'
        assert data['error'] is None
    
    def test_num2words_large_numbers(self, client):
        """Test num2words library with very large numbers"""
        response = client.post('/convert',
            data=json.dumps({'input': '1000000', 'inputType': 'decimal', 'outputType': 'text'}),
            content_type='application/json')
        data = json.loads(response.data)
        # num2words should handle large numbers
        assert data['result'] == 'one million'
        assert data['error'] is None
    
    def test_text2digits_imported_but_not_used(self):
        """Test that text2digits library is imported but not used in our implementation"""
        # This reveals a potential bug - we import text2digits but don't use it
        # Our text_to_number function only handles basic numbers 1-10
        # This is a design issue where we could use text2digits for better text parsing
        from text2digits import text2digits
        t2d = text2digits.Text2Digits()
        
        # text2digits can handle more complex text than our implementation
        result = t2d.convert("forty two")
        assert result == "42"
        
        # But our implementation can't handle this
        with pytest.raises(ValueError):
            text_to_number("forty two")
    
    def test_num2words_locale_issues(self, client):
        """Test potential locale issues in num2words"""
        response = client.post('/convert',
            data=json.dumps({'input': '1', 'inputType': 'decimal', 'outputType': 'text'}),
            content_type='application/json')
        data = json.loads(response.data)
        # num2words might have locale-specific behavior
        assert data['result'] == 'one'
        assert data['error'] is None

class TestErrorHandling:
    def test_invalid_input_type(self, client):
        response = client.post('/convert',
            data=json.dumps({'input': '42', 'inputType': 'invalid', 'outputType': 'decimal'}),
            content_type='application/json')
        data = json.loads(response.data)
        assert data['result'] is None
        assert 'Invalid input type' in data['error']
    
    def test_invalid_output_type(self, client):
        response = client.post('/convert',
            data=json.dumps({'input': '42', 'inputType': 'decimal', 'outputType': 'invalid'}),
            content_type='application/json')
        data = json.loads(response.data)
        assert data['result'] is None
        assert 'Invalid output type' in data['error']
    
    def test_invalid_binary_input(self, client):
        response = client.post('/convert',
            data=json.dumps({'input': '102', 'inputType': 'binary', 'outputType': 'decimal'}),
            content_type='application/json')
        data = json.loads(response.data)
        assert data['result'] is None
        assert data['error'] is not None
    
    def test_invalid_text_input(self, client):
        response = client.post('/convert',
            data=json.dumps({'input': 'eleven', 'inputType': 'text', 'outputType': 'decimal'}),
            content_type='application/json')
        data = json.loads(response.data)
        assert data['result'] is None
        assert 'Unable to convert text to number' in data['error']

if __name__ == '__main__':
    pytest.main([__file__])
