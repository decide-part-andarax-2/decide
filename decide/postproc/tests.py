from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework.test import APITestCase

from base import mods


class PostProcTestCase(APITestCase):

    def setUp(self):
        self.client = APIClient()
        mods.mock_query(self.client)

    def tearDown(self):
        self.client = None

    def test_identity(self):
        data = {
            'type': 'IDENTITY',
            'options': [
                {'option': 'Option 1', 'number': 1, 'votes': 5},
                {'option': 'Option 2', 'number': 2, 'votes': 0},
                {'option': 'Option 3', 'number': 3, 'votes': 3},
                {'option': 'Option 4', 'number': 4, 'votes': 2},
                {'option': 'Option 5', 'number': 5, 'votes': 5},
                {'option': 'Option 6', 'number': 6, 'votes': 1},
            ]
        }

        expected_result = [
            {'option': 'Option 1', 'number': 1, 'votes': 5, 'postproc': 5},
            {'option': 'Option 5', 'number': 5, 'votes': 5, 'postproc': 5},
            {'option': 'Option 3', 'number': 3, 'votes': 3, 'postproc': 3},
            {'option': 'Option 4', 'number': 4, 'votes': 2, 'postproc': 2},
            {'option': 'Option 6', 'number': 6, 'votes': 1, 'postproc': 1},
            {'option': 'Option 2', 'number': 2, 'votes': 0, 'postproc': 0},
        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)

        values = response.json()
        self.assertEqual(values, expected_result)



    def test_dhont1(self):
        data = {
            'type': 'DHONT',
            'seats': 10,
            'options': [
                { 'option': 'Option 1', 'number': 1, 'votes': 10 },
                { 'option': 'Option 2', 'number': 2, 'votes': 0 },
                { 'option': 'Option 3', 'number': 3, 'votes': 7 },
                { 'option': 'Option 4', 'number': 4, 'votes': 2 },
                { 'option': 'Option 5', 'number': 5, 'votes': 5 },
                { 'option': 'Option 6', 'number': 6, 'votes': 1 },
            ]
        }
        expected_result = [
            { 'option': 'Option 1', 'number': 1, 'votes': 10, 'postproc': 5 },
            { 'option': 'Option 3', 'number': 3, 'votes': 7, 'postproc': 3 },
            { 'option': 'Option 5', 'number': 5, 'votes': 5, 'postproc': 2 },
            { 'option': 'Option 4', 'number': 4, 'votes': 2, 'postproc': 0 },
            { 'option': 'Option 6', 'number': 6, 'votes': 1, 'postproc': 0 },
            { 'option': 'Option 2', 'number': 2, 'votes': 0, 'postproc': 0 },
        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)

        values = response.json()
        self.assertEqual(values, expected_result)

    def test_dhont_2(self):
        seats = 5
        data = {
            'type': 'DHONT',
            'seats': seats,
            'options': [
                {'option': 'Option 1', 'number': 1, 'votes': 10},
                {'option': 'Option 2', 'number': 2, 'votes': 0},
                {'option': 'Option 3', 'number': 3, 'votes': 6},
                {'option': 'Option 4', 'number': 4, 'votes': 4},
                {'option': 'Option 5', 'number': 5, 'votes': 10},
                {'option': 'Option 6', 'number': 6, 'votes': 2},
                {'option': 'Option 7', 'number': 7, 'votes': 6},
            ]
        }

        expected_result = [
            {'option': 'Option 1', 'number': 1, 'votes': 10, 'postproc': 2},
            {'option': 'Option 5', 'number': 5, 'votes': 10, 'postproc': 1},
            {'option': 'Option 3', 'number': 3, 'votes': 6, 'postproc': 1},
            {'option': 'Option 7', 'number': 7, 'votes': 6, 'postproc': 1},
            {'option': 'Option 4', 'number': 4, 'votes': 4, 'postproc': 0},
            {'option': 'Option 6', 'number': 6, 'votes': 2, 'postproc': 0},
            {'option': 'Option 2', 'number': 2, 'votes': 0, 'postproc': 0},
        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)

        values = response.json()
        self.assertEqual(values, expected_result)

    def test_dhont_3(self):
        seats = 9
        data = {
            'type': 'DHONT',
            'seats': seats,
            'options': [
                {'option': 'Option 1', 'number': 1, 'votes': 100},
                {'option': 'Option 2', 'number': 2, 'votes': 122},
                {'option': 'Option 3', 'number': 3, 'votes': 500},
                {'option': 'Option 4', 'number': 4, 'votes': 279},
                {'option': 'Option 5', 'number': 5, 'votes': 927},
            ]
        }

        expected_result = [
            {'option': 'Option 5', 'number': 5, 'votes': 927, 'postproc': 5},
            {'option': 'Option 3', 'number': 3, 'votes': 500, 'postproc': 3},
            {'option': 'Option 4', 'number': 4, 'votes': 279, 'postproc': 1},
            {'option': 'Option 2', 'number': 2, 'votes': 122, 'postproc': 0},
            {'option': 'Option 1', 'number': 1, 'votes': 100, 'postproc': 0},
        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)

        values = response.json()
        self.assertEqual(values, expected_result)

    def test_dhont_4(self):
        seats = 100
        data = {
            'type': 'DHONT',
            'seats': seats,
            'options': [
                {'option': 'Option 1', 'number': 1, 'votes': 7900},
                {'option': 'Option 2', 'number': 2, 'votes': 8300},
                {'option': 'Option 3', 'number': 3, 'votes': 5000},
                {'option': 'Option 4', 'number': 4, 'votes': 4300},
                {'option': 'Option 5', 'number': 5, 'votes': 7100},
            ]
        }

        expected_result = [
            {'option': 'Option 2', 'number': 2, 'votes': 8300, 'postproc': 26},
            {'option': 'Option 1', 'number': 1, 'votes': 7900, 'postproc': 24},
            {'option': 'Option 5', 'number': 5, 'votes': 7100, 'postproc': 22},
            {'option': 'Option 3', 'number': 3, 'votes': 5000, 'postproc': 15},
            {'option': 'Option 4', 'number': 4, 'votes': 4300, 'postproc': 13},
        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)

        values = response.json()
        self.assertEqual(values, expected_result)

    # Test en el que no se define la variable type en el json data
    def test_no_type(self):
        seats = 5
        data = {
            'seats': seats,
            'options': [
                {'option': 'Option 1', 'number': 1, 'votes': 9},
                {'option': 'Option 2', 'number': 2, 'votes': 0},
                {'option': 'Option 3', 'number': 3, 'votes': 6},
                {'option': 'Option 4', 'number': 4, 'votes': 4},
                {'option': 'Option 5', 'number': 5, 'votes': 8},
                {'option': 'Option 6', 'number': 6, 'votes': 2},
                {'option': 'Option 7', 'number': 7, 'votes': 5},

            ]
        }
        expected_result = {}

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 400)

        values = response.json()
        self.assertEqual(values, expected_result)

    def test_relativa1(self):
        data = {
            'type': 'RELATIVA',
            'options': [
                { 'option': 'Option 1', 'number': 1, 'votes': 7 },
                { 'option': 'Option 2', 'number': 2, 'votes': 4 },
                { 'option': 'Option 3', 'number': 3, 'votes': 6 },
            ]
        }

        expected_result = [
            { 'option': 'Option 1', 'number': 1, 'votes': 7, 'postproc': 1 },
            { 'option': 'Option 3', 'number': 3, 'votes': 6, 'postproc': 0 },
            { 'option': 'Option 2', 'number': 2, 'votes': 4, 'postproc': 0 },
        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)

        values = response.json()
        self.assertEqual(values, expected_result)

    def test_relativa2(self):
        data = {
            'type': 'RELATIVA',
            'options': [
                { 'option': 'Option 1', 'number': 1, 'votes': 2 },
                { 'option': 'Option 2', 'number': 2, 'votes': 8 },
            ]
        }

        expected_result = [
            { 'option': 'Option 2', 'number': 2, 'votes': 8, 'postproc': 1 },
            { 'option': 'Option 1', 'number': 1, 'votes': 2, 'postproc': 0 },
        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)
        values = response.json()
        self.assertEqual(values, expected_result)

    def test_relativa3(self):
        data = {
            'type': 'RELATIVA',
            'options': [
                { 'option': 'Option 1', 'number': 1, 'votes': 1 },
                { 'option': 'Option 2', 'number': 2, 'votes': 2 },
                { 'option': 'Option 3', 'number': 3, 'votes': 3 },
                { 'option': 'Option 4', 'number': 4, 'votes': 4 },
            ]
        }

        expected_result = [
            { 'option': 'Option 4', 'number': 4, 'votes': 4, 'postproc': 1 },
            { 'option': 'Option 3', 'number': 3, 'votes': 3, 'postproc': 0 },
            { 'option': 'Option 2', 'number': 2, 'votes': 2, 'postproc': 0 },
            { 'option': 'Option 1', 'number': 1, 'votes': 1, 'postproc': 0 },
        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)

        values = response.json()
        self.assertEqual(values, expected_result)

    def test_relativa4(self):
        data = {
            'type': 'RELATIVA',
            'options': [
                { 'option': 'Option 1', 'number': 1, 'votes': 0 },
                { 'option': 'Option 2', 'number': 2, 'votes': 0 },
                { 'option': 'Option 3', 'number': 3, 'votes': 8 },
                { 'option': 'Option 4', 'number': 4, 'votes': 2 },
                { 'option': 'Option 5', 'number': 5, 'votes': 0 },
            ]
        }

        expected_result = [
                { 'option': 'Option 3', 'number': 3, 'votes': 8, 'postproc': 1 },
                { 'option': 'Option 4', 'number': 4, 'votes': 2, 'postproc': 0 },
                { 'option': 'Option 1', 'number': 1, 'votes': 0, 'postproc': 0 },
                { 'option': 'Option 2', 'number': 2, 'votes': 0, 'postproc': 0 },
                { 'option': 'Option 5', 'number': 5, 'votes': 0, 'postproc': 0 },
        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)
        values = response.json()
        self.assertEqual(values, expected_result)

    def test_relativa5(self):
        data = {
            'type': 'RELATIVA',
            'options': [
                { 'option': 'Option 1', 'number': 1, 'votes': 0 },
                { 'option': 'Option 2', 'number': 2, 'votes': 0 },
                { 'option': 'Option 3', 'number': 3, 'votes': 0 },
                { 'option': 'Option 4', 'number': 4, 'votes': 0 },
                { 'option': 'Option 5', 'number': 5, 'votes': 0 },
                { 'option': 'Option 6', 'number': 6, 'votes': 0 },
                { 'option': 'Option 7', 'number': 7, 'votes': 0 },
                { 'option': 'Option 8', 'number': 8, 'votes': 0 },
                { 'option': 'Option 9', 'number': 9, 'votes': 1 },
                { 'option': 'Option 10', 'number': 10, 'votes': 0 },
                { 'option': 'Option 11', 'number': 11, 'votes': 0 },
                { 'option': 'Option 12', 'number': 12, 'votes': 0 },
                { 'option': 'Option 13', 'number': 13, 'votes': 0 },
                { 'option': 'Option 14', 'number': 14, 'votes': 0 },
                { 'option': 'Option 15', 'number': 15, 'votes': 0 },
            ]
        }

        expected_result = [
                { 'option': 'Option 9', 'number':9, 'votes': 1, 'postproc': 1 },
                { 'option': 'Option 1', 'number': 1, 'votes': 0, 'postproc': 0 },
                { 'option': 'Option 2', 'number': 2, 'votes': 0, 'postproc': 0 },
                { 'option': 'Option 3', 'number': 3, 'votes': 0, 'postproc': 0 },
                { 'option': 'Option 4', 'number': 4, 'votes': 0, 'postproc': 0 },
                { 'option': 'Option 5', 'number': 5, 'votes': 0, 'postproc': 0 },
                { 'option': 'Option 6', 'number': 6, 'votes': 0, 'postproc': 0 },
                { 'option': 'Option 7', 'number': 7, 'votes': 0, 'postproc': 0 },
                { 'option': 'Option 8', 'number': 8, 'votes': 0, 'postproc': 0 },
                { 'option': 'Option 10', 'number': 10, 'votes': 0, 'postproc': 0 },
                { 'option': 'Option 11', 'number': 11, 'votes': 0, 'postproc': 0 },
                { 'option': 'Option 12', 'number': 12, 'votes': 0, 'postproc': 0 },
                { 'option': 'Option 13', 'number': 13, 'votes': 0, 'postproc': 0 },
                { 'option': 'Option 14', 'number': 14, 'votes': 0, 'postproc': 0 },
                { 'option': 'Option 15', 'number': 15, 'votes': 0, 'postproc': 0 },
        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)
        values = response.json()
        self.assertEqual(values, expected_result)

    def test_relativa6(self):
        data = {
            'type': 'RELATIVA',
            'options': [
                { 'option': 'Option 1', 'number': 1, 'votes': 70 },
                { 'option': 'Option 2', 'number': 2, 'votes': 800 },
                { 'option': 'Option 3', 'number': 3, 'votes': 345 },
                { 'option': 'Option 4', 'number': 4, 'votes': 200 },
                { 'option': 'Option 5', 'number': 5, 'votes': 729 },
                { 'option': 'Option 6', 'number': 6, 'votes': 273},
            ]
        }

        expected_result = [
                { 'option': 'Option 2', 'number': 2, 'votes': 800, 'postproc': 1 },
                { 'option': 'Option 5', 'number': 5, 'votes': 729, 'postproc': 0 },
                { 'option': 'Option 3', 'number': 3, 'votes': 345, 'postproc': 0 },
                { 'option': 'Option 6', 'number': 6, 'votes': 273, 'postproc': 0 },
                { 'option': 'Option 4', 'number': 4, 'votes': 200, 'postproc': 0 },
                { 'option': 'Option 1', 'number': 1, 'votes': 70, 'postproc': 0 },
        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)
        values = response.json()
        self.assertEqual(values, expected_result)
        
    def test_relativa7(self):
        data = {
            'type': 'RELATIVA',
            'options': [
                { 'option': 'Option 1', 'number': 1, 'votes': 7230 },
                { 'option': 'Option 2', 'number': 2, 'votes': 82300 },
                { 'option': 'Option 3', 'number': 3, 'votes': 3445 },
                { 'option': 'Option 4', 'number': 4, 'votes': 20320 },
                { 'option': 'Option 5', 'number': 5, 'votes': 72952 },
                { 'option': 'Option 6', 'number': 6, 'votes': 27213},
                { 'option': 'Option 7', 'number': 7, 'votes': 83200 },
                { 'option': 'Option 8', 'number': 8, 'votes': 34455 },
                { 'option': 'Option 9', 'number': 9, 'votes': 20321 },
                { 'option': 'Option 10', 'number': 10, 'votes': 729123 },
                { 'option': 'Option 11', 'number': 11, 'votes': 27243},
                { 'option': 'Option 12', 'number': 12, 'votes': 802120 },
                { 'option': 'Option 13', 'number': 13, 'votes': 343235 },
                { 'option': 'Option 14', 'number': 14, 'votes': 20230 },
                { 'option': 'Option 15', 'number': 15, 'votes': 721239 },
                { 'option': 'Option 16', 'number': 16, 'votes': 273123},
            ]
        }

        expected_result = [
                { 'option': 'Option 12', 'number': 12, 'votes': 802120, 'postproc': 1 },
                { 'option': 'Option 10', 'number': 10, 'votes': 729123, 'postproc': 0 },
                { 'option': 'Option 15', 'number': 15, 'votes': 721239, 'postproc': 0 },
                { 'option': 'Option 13', 'number': 13, 'votes': 343235, 'postproc': 0 },
                { 'option': 'Option 16', 'number': 16, 'votes': 273123, 'postproc': 0 },
                { 'option': 'Option 7', 'number': 7, 'votes': 83200, 'postproc': 0 },
                { 'option': 'Option 2', 'number': 2, 'votes': 82300, 'postproc': 0 },
                { 'option': 'Option 5', 'number': 5, 'votes': 72952, 'postproc': 0 },
                { 'option': 'Option 8', 'number': 8, 'votes': 34455, 'postproc': 0 },
                { 'option': 'Option 11', 'number': 11, 'votes': 27243, 'postproc': 0 },
                { 'option': 'Option 6', 'number': 6, 'votes': 27213, 'postproc': 0 },
                { 'option': 'Option 9', 'number': 9, 'votes': 20321, 'postproc': 0 },
                { 'option': 'Option 4', 'number': 4, 'votes': 20320, 'postproc': 0 },
                { 'option': 'Option 14', 'number': 14, 'votes': 20230, 'postproc': 0 },
                { 'option': 'Option 1', 'number': 1, 'votes': 7230, 'postproc': 0 },
                { 'option': 'Option 3', 'number': 3, 'votes': 3445, 'postproc': 0 },
              
        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)
        values = response.json()
        self.assertEqual(values, expected_result)

    def test_relativa_no_options(self):
        data = {
            'type': 'RELATIVA',
        }

        expected_result = {}

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 400)

        values = response.json()
        self.assertEqual(values, expected_result)



    def test_absoluta1(self):
        data = {
            'type': 'ABSOLUTA',
            'options': [
                { 'option': 'Option 1', 'number': 1, 'votes': 2 },
                { 'option': 'Option 2', 'number': 2, 'votes': 2 },
            ]
        }

        expected_result = [
                { 'option': 'Option 1', 'number': 1, 'votes': 2, 'postproc': 0 },
                { 'option': 'Option 2', 'number': 2, 'votes': 2, 'postproc': 0 },
        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)
        values = response.json()
        self.assertEqual(values, expected_result)

    def test_absoluta2(self):
        data = {
            'type': 'ABSOLUTA',
            'options': [
                {'option': 'Option 1', 'number': 1, 'votes': 100},
                {'option': 'Option 2', 'number': 2, 'votes': 0},
                {'option': 'Option 3', 'number': 3, 'votes': 6},
                {'option': 'Option 4', 'number': 4, 'votes': 4},
                {'option': 'Option 5', 'number': 5, 'votes': 10},
                {'option': 'Option 6', 'number': 6, 'votes': 2},
                {'option': 'Option 7', 'number': 7, 'votes': 6},
            ]
        }

        expected_result = [
                {'option': 'Option 1', 'number': 1, 'votes': 100, 'postproc': 1},
                {'option': 'Option 5', 'number': 5, 'votes': 10, 'postproc': 0},
                {'option': 'Option 3', 'number': 3, 'votes': 6, 'postproc': 0},
                {'option': 'Option 7', 'number': 7, 'votes': 6, 'postproc': 0},
                {'option': 'Option 4', 'number': 4, 'votes': 4, 'postproc': 0},
                {'option': 'Option 6', 'number': 6, 'votes': 2, 'postproc': 0},
                {'option': 'Option 2', 'number': 2, 'votes': 0, 'postproc': 0},

        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)
        values = response.json()
        self.assertEqual(values, expected_result)

    def test_absoluta3(self):
        data = {
            'type': 'ABSOLUTA',
            'options': [
                {'option': 'Option 1', 'number': 1, 'votes': 74},
                {'option': 'Option 2', 'number': 2, 'votes': 12},
                {'option': 'Option 3', 'number': 3, 'votes': 89},
                {'option': 'Option 4', 'number': 4, 'votes': 27},
                {'option': 'Option 5', 'number': 5, 'votes': 46},
                {'option': 'Option 6', 'number': 6, 'votes': 21},
                {'option': 'Option 7', 'number': 7, 'votes': 17},
                {'option': 'Option 8', 'number': 8, 'votes': 41},
            ]
        }

        expected_result = [
                {'option': 'Option 3', 'number': 3, 'votes': 89, 'postproc': 0},
                {'option': 'Option 1', 'number': 1, 'votes': 74, 'postproc': 0},
                {'option': 'Option 5', 'number': 5, 'votes': 46, 'postproc': 0},
                {'option': 'Option 8', 'number': 8, 'votes': 41, 'postproc': 0},
                {'option': 'Option 4', 'number': 4, 'votes': 27, 'postproc': 0},
                {'option': 'Option 6', 'number': 6, 'votes': 21, 'postproc': 0},
                {'option': 'Option 7', 'number': 7, 'votes': 17, 'postproc': 0},
                {'option': 'Option 2', 'number': 2, 'votes': 12, 'postproc': 0},
        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)
        values = response.json()
        self.assertEqual(values, expected_result)

    def test_absoluta4(self):
        data = {
            'type': 'ABSOLUTA',
            'options': [
                {'option': 'PP', 'number': 1, 'votes': 10867344},
                {'option': 'PSOE', 'number': 2, 'votes': 7003511},
                {'option': 'CiU', 'number': 3, 'votes': 1015691},
                {'option': 'IU', 'number': 4, 'votes': 1686040},
            ]
        }

        expected_result = [
                {'option': 'PP', 'number': 1, 'votes': 10867344, 'postproc': 1},
                {'option': 'PSOE', 'number': 2, 'votes': 7003511, 'postproc': 0},
                {'option': 'IU', 'number': 4, 'votes': 1686040, 'postproc': 0},
                {'option': 'CiU', 'number': 3, 'votes': 1015691, 'postproc': 0},
        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)
        values = response.json()
        self.assertEqual(values, expected_result)

    # Test en el que no se le pasa la variable options en el json data
    def test_no_options(self):
        seats = 5
        data = {
            'type': 'DHONT',
            'seats': seats
        }
        expected_result = {}

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 400)

        values = response.json()
        self.assertEqual(values, expected_result)

     # Test en el que no se le pasa la variable seats en el json data
    def test_no_seats(self):
        data = {
            'type': 'DHONT',
            'options': [
                {'option': 'Option 1', 'number': 1, 'votes': 18},
                {'option': 'Option 2', 'number': 2, 'votes': 3},
                {'option': 'Option 3', 'number': 3, 'votes': 6},

            ]
        }
        expected_result = {}

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 400)

        values = response.json()
        self.assertEqual(values, expected_result)


    def test_paridad(self):

        candidates1 = [{'name': 'Candidate1', 'gender': 'M'},
                       {'name': 'Candidate2', 'gender': 'H'},
                       {'name': 'Candidate3', 'gender': 'M'},
                       {'name': 'Candidate4', 'gender': 'H'},
                       {'name': 'Candidate5', 'gender': 'H'}]

        candidates2 = [{'name': 'Candidate6', 'gender': 'H'},
                       {'name': 'Candidate7', 'gender': 'M'},
                       {'name': 'Candidate8', 'gender': 'M'},
                       {'name': 'Candidate9', 'gender': 'H'},
                       {'name': 'Candidate10', 'gender': 'H'}]

        candidates3 = [{'name': 'Candidate11', 'gender': 'H'},
                       {'name': 'Candidate12', 'gender': 'H'},
                       {'name': 'Candidate13', 'gender': 'M'},
                       {'name': 'Candidate14', 'gender': 'M'},
                       {'name': 'Candidate15', 'gender': 'M'}]

        candidates4 = [{'name': 'Candidate16', 'gender': 'H'},
                       {'name': 'Candidate17', 'gender': 'M'},
                       {'name': 'Candidate18', 'gender': 'M'},
                       {'name': 'Candidate19', 'gender': 'H'},
                       {'name': 'Candidate20', 'gender': 'M'}]

        candidates5 = [{'name': 'Candidate21', 'gender': 'M'},
                       {'name': 'Candidate22', 'gender': 'H'},
                       {'name': 'Candidate23', 'gender': 'M'},
                       {'name': 'Candidate24', 'gender': 'H'},
                       {'name': 'Candidate25', 'gender': 'M'}]

        candidates6 = [{'name': 'Candidate26', 'gender': 'M'},
                       {'name': 'Candidate27', 'gender': 'M'},
                       {'name': 'Candidate28', 'gender': 'M'},
                       {'name': 'Candidate29', 'gender': 'H'},
                       {'name': 'Candidate30', 'gender': 'M'}]
        data = {
            'type': 'DHONT',
            'paridad': True,
            'seats': 10,
            'options': [
                { 'option': 'Option 1', 'number': 1, 'votes': 10, 'candidates': candidates1 },
                { 'option': 'Option 2', 'number': 2, 'votes': 0, 'candidates': candidates2 },
                { 'option': 'Option 3', 'number': 3, 'votes': 7, 'candidates': candidates3 },
                { 'option': 'Option 4', 'number': 4, 'votes': 2, 'candidates': candidates4 },
                { 'option': 'Option 5', 'number': 5, 'votes': 5, 'candidates': candidates5 },
                { 'option': 'Option 6', 'number': 6, 'votes': 1, 'candidates': candidates6 },
            ]
        }

        seated1 = [{'name': 'Candidate1', 'gender': 'M'},
                       {'name': 'Candidate2', 'gender': 'H'},
                       {'name': 'Candidate3', 'gender': 'M'},
                       {'name': 'Candidate4', 'gender': 'H'},
                       {'name': 'Candidate5', 'gender': 'H'}]

        seated3 = [{'name': 'Candidate11', 'gender': 'H'},
                       {'name': 'Candidate13', 'gender': 'M'},
                       {'name': 'Candidate12', 'gender': 'H'},
                       ]

        seated5 = [{'name': 'Candidate21', 'gender': 'M'},
                       {'name': 'Candidate22', 'gender': 'H'},
                       ]

        expected_result = [
            { 'option': 'Option 1', 'number': 1, 'votes': 10, 'candidates': candidates1, 'postproc': 5, 'seated': seated1 },
            { 'option': 'Option 3', 'number': 3, 'votes': 7, 'candidates': candidates3 , 'postproc': 3, 'seated': seated3  },
            { 'option': 'Option 5', 'number': 5, 'votes': 5, 'candidates': candidates5, 'postproc': 2, 'seated': seated5  },
            { 'option': 'Option 4', 'number': 4, 'votes': 2, 'candidates': candidates4, 'postproc': 0, 'seated': []},
            { 'option': 'Option 6', 'number': 6, 'votes': 1, 'candidates': candidates6 , 'postproc': 0, 'seated': []},
            { 'option': 'Option 2', 'number': 2, 'votes': 0, 'candidates': candidates2 , 'postproc': 0, 'seated': []},
          ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)
        values = response.json()
        self.assertEqual(values, expected_result)

    def test_paridad2(self):

        candidates1 = [{'name': 'Candidate1', 'gender': 'M'},
                       {'name': 'Candidate2', 'gender': 'H'},
                       {'name': 'Candidate3', 'gender': 'M'},
                       {'name': 'Candidate4', 'gender': 'H'},
                       {'name': 'Candidate5', 'gender': 'H'}]

        candidates2 = [{'name': 'Candidate6', 'gender': 'H'},
                       {'name': 'Candidate7', 'gender': 'M'},
                       {'name': 'Candidate8', 'gender': 'M'},
                       {'name': 'Candidate9', 'gender': 'H'},
                       {'name': 'Candidate10', 'gender': 'H'}]

        candidates3 = [{'name': 'Candidate11', 'gender': 'H'},
                       {'name': 'Candidate12', 'gender': 'H'},
                       {'name': 'Candidate13', 'gender': 'M'},
                       {'name': 'Candidate14', 'gender': 'M'},
                       {'name': 'Candidate15', 'gender': 'M'}]

        candidates4 = [{'name': 'Candidate16', 'gender': 'H'},
                       {'name': 'Candidate17', 'gender': 'M'},
                       {'name': 'Candidate18', 'gender': 'M'},
                       {'name': 'Candidate19', 'gender': 'H'},
                       {'name': 'Candidate20', 'gender': 'M'}]

        candidates5 = [{'name': 'Candidate21', 'gender': 'M'},
                       {'name': 'Candidate22', 'gender': 'H'},
                       {'name': 'Candidate23', 'gender': 'M'},
                       {'name': 'Candidate24', 'gender': 'H'},
                       {'name': 'Candidate25', 'gender': 'M'}]

        candidates6 = [{'name': 'Candidate26', 'gender': 'M'},
                       {'name': 'Candidate27', 'gender': 'M'},
                       {'name': 'Candidate28', 'gender': 'M'},
                       {'name': 'Candidate29', 'gender': 'H'},
                       {'name': 'Candidate30', 'gender': 'M'}]

        candidates7 = [{'name': 'Candidate31', 'gender': 'M'},
                       {'name': 'Candidate32', 'gender': 'H'},
                       {'name': 'Candidate33', 'gender': 'M'},
                       {'name': 'Candidate34', 'gender': 'H'},
                       {'name': 'Candidate35', 'gender': 'H'}]
        data = {
            'type': 'DHONT',
            'paridad': True,
            'seats': 5,
            'options': [
                {'option': 'Option 1', 'number': 1, 'votes': 10, 'candidates': candidates1},
                {'option': 'Option 2', 'number': 2, 'votes': 0, 'candidates': candidates2},
                {'option': 'Option 3', 'number': 3, 'votes': 6, 'candidates': candidates3},
                {'option': 'Option 4', 'number': 4, 'votes': 4, 'candidates': candidates4},
                {'option': 'Option 5', 'number': 5, 'votes': 10, 'candidates': candidates5},
                {'option': 'Option 6', 'number': 6, 'votes': 2, 'candidates': candidates6},
                {'option': 'Option 7', 'number': 7, 'votes': 6, 'candidates': candidates7},
            ]
        }

        seated1 = [{'name': 'Candidate1', 'gender': 'M'},
                       {'name': 'Candidate2', 'gender': 'H'},
                       ]

        seated3 = [{'name': 'Candidate11', 'gender': 'H'},
                       ]

        seated5 = [{'name': 'Candidate21', 'gender': 'M'},
                       ]

        seated7 = [{'name': 'Candidate31', 'gender': 'M'},
                      ]

        expected_result = [
            {'option': 'Option 1', 'number': 1, 'votes': 10, 'candidates': candidates1, 'postproc': 2,'seated': seated1},
            {'option': 'Option 5', 'number': 5, 'votes': 10, 'candidates': candidates5, 'postproc': 1,'seated': seated5},
            {'option': 'Option 3', 'number': 3, 'votes': 6, 'candidates': candidates3, 'postproc': 1,'seated': seated3},
            {'option': 'Option 7', 'number': 7, 'votes': 6, 'candidates': candidates7, 'postproc': 1,'seated': seated7},
            {'option': 'Option 4', 'number': 4, 'votes': 4, 'candidates': candidates4, 'postproc': 0,'seated': []},
            {'option': 'Option 6', 'number': 6, 'votes': 2, 'candidates': candidates6, 'postproc': 0,'seated': []},
            {'option': 'Option 2', 'number': 2, 'votes': 0, 'candidates': candidates2, 'postproc': 0,'seated': []},
           ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)
        values = response.json()
        self.assertEqual(values, expected_result)

    def test_borda1(self):
        data = {
            'type': 'BORDA',
            'order_options': [
                {'option': 'Option 1', 'number': 1, 'order_number': '1', 'votes': 80},
                {'option': 'Option 2', 'number': 2, 'order_number': '1', 'votes': 15},
                {'option': 'Option 3', 'number': 3, 'order_number': '1', 'votes': 5},
                {'option': 'Option 1', 'number': 1, 'order_number': '2', 'votes': 5},
                {'option': 'Option 2', 'number': 2, 'order_number': '2', 'votes': 80},
                {'option': 'Option 3', 'number': 3, 'order_number': '2', 'votes': 15},
                {'option': 'Option 1', 'number': 1, 'order_number': '3', 'votes': 15},
                {'option': 'Option 2', 'number': 2, 'order_number': '3', 'votes': 5},
                {'option': 'Option 3', 'number': 3, 'order_number': '3', 'votes': 80},
            ]
        }

        expected_result = [
                {'option': 'Option 1', 'number': 1, 'order_number': '1', 'votes': 80, 'postproc': 265},
                {'option': 'Option 2', 'number': 2, 'order_number': '1', 'votes': 15, 'postproc': 210},
                {'option': 'Option 3', 'number': 3, 'order_number': '1', 'votes': 5, 'postproc': 125},
        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)
        values = response.json()
        print(values)
        self.assertEqual(values, expected_result)

    def test_borda2(self):
        data = {
            'type': 'BORDA',
            'order_options': [
                {'option': 'Option 1', 'number': 1, 'order_number': '1', 'votes': 50},
                {'option': 'Option 2', 'number': 2, 'order_number': '1', 'votes': 50},
                {'option': 'Option 3', 'number': 3, 'order_number': '1', 'votes': 0},
                {'option': 'Option 1', 'number': 1, 'order_number': '2', 'votes': 20},
                {'option': 'Option 2', 'number': 2, 'order_number': '2', 'votes': 20},
                {'option': 'Option 3', 'number': 3, 'order_number': '2', 'votes': 60},
                {'option': 'Option 1', 'number': 1, 'order_number': '3', 'votes': 30},
                {'option': 'Option 2', 'number': 2, 'order_number': '3', 'votes': 30},
                {'option': 'Option 3', 'number': 3, 'order_number': '3', 'votes': 40},
            ]
        }

        expected_result = [
                {'option': 'Option 1', 'number': 1, 'order_number': '1', 'votes': 50, 'postproc': 220},
                {'option': 'Option 2', 'number': 2, 'order_number': '1', 'votes': 50, 'postproc': 220},
                {'option': 'Option 3', 'number': 3, 'order_number': '1', 'votes': 0, 'postproc': 160},
        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)
        values = response.json()
        self.assertEqual(values, expected_result)

    #Test en el que se le pasa una votación normal, no una con order_options
    def test_no_order_options(self):
        data = {
            'type': 'BORDA',
            'options': [
                {'option': 'Option 1', 'number': 1, 'votes': 10},
                {'option': 'Option 2', 'number': 2, 'votes': 5},
                {'option': 'Option 3', 'number': 3, 'votes': 6},
                {'option': 'Option 4', 'number': 4, 'votes': 8},
                {'option': 'Option 5', 'number': 5, 'votes': 4},
                {'option': 'Option 6', 'number': 6, 'votes': 6},
                {'option': 'Option 7', 'number': 7, 'votes': 2},
                {'option': 'Option 8', 'number': 8, 'votes': 0},

            ],
            'order_options': []
        }

        expected_result = {}

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 400)

        values = response.json()
        self.assertEqual(values, expected_result)

    #Test en el que no se le pasa tipo a una votación de borda
    def test_borda_no_type(self):

        data = {
            'order_options': [
                {'option': 'Option 1', 'number': 1, 'order_number': '1', 'votes': 50},
                {'option': 'Option 2', 'number': 2, 'order_number': '1', 'votes': 50},
                {'option': 'Option 3', 'number': 3, 'order_number': '1', 'votes': 0},
                {'option': 'Option 1', 'number': 1, 'order_number': '2', 'votes': 20},
                {'option': 'Option 2', 'number': 2, 'order_number': '2', 'votes': 20},
                {'option': 'Option 3', 'number': 3, 'order_number': '2', 'votes': 60},
                {'option': 'Option 1', 'number': 1, 'order_number': '3', 'votes': 30},
                {'option': 'Option 2', 'number': 2, 'order_number': '3', 'votes': 30},
                {'option': 'Option 3', 'number': 3, 'order_number': '3', 'votes': 40},
            ]
        }

        expected_result = {}

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 400)

        values = response.json()
        self.assertEqual(values, expected_result)

    #Test en el que todos los votos son 0, así viene de votación al no haber ningún
    #equipo de cabina que pueda realizar votaciones
    def test_borda_cero_votos(self):
        data = {
            'type': 'BORDA',
            'order_options': [
                {'option': 'Option 1', 'number': 1, 'order_number': '1', 'votes': 0},
                {'option': 'Option 2', 'number': 2, 'order_number': '2', 'votes': 0},
                {'option': 'Option 3', 'number': 3, 'order_number': '3', 'votes': 0},
                {'option': 'Option 4', 'number': 4, 'order_number': '4', 'votes': 0},
                {'option': 'Option 5', 'number': 5, 'order_number': '5', 'votes': 0},
            ]
        }

        expected_result = [
            {'option': 'Option 1', 'number': 1, 'order_number': '1', 'votes': 0, 'postproc': 0},
            {'option': 'Option 2', 'number': 2, 'order_number': '2', 'votes': 0, 'postproc': 0},
            {'option': 'Option 3', 'number': 3, 'order_number': '3', 'votes': 0, 'postproc': 0},
            {'option': 'Option 4', 'number': 4, 'order_number': '4', 'votes': 0, 'postproc': 0},
            {'option': 'Option 5', 'number': 5, 'order_number': '5', 'votes': 0, 'postproc': 0}]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)
        values = response.json()
        print(values)
        self.assertEqual(values, expected_result)

    def test_substrat_1(self):
        seats = 8
        data = {
            'seats': seats,
            'type': 'SUBTRAC',
            'options': [
                {'option': 'Option 1', 'number': 1, 'votes_add': 10, 'votes_subtract':12},
                {'option': 'Option 2', 'number': 2, 'votes_add': 5, 'votes_subtract':2},
                {'option': 'Option 3', 'number': 3, 'votes_add': 6, 'votes_subtract':1},
                {'option': 'Option 4', 'number': 4, 'votes_add': 8, 'votes_subtract':2},
                {'option': 'Option 5', 'number': 5, 'votes_add': 2, 'votes_subtract':0},

            ]
        }

        expected_result = [
            {'option': 'Option 4', 'number': 4, 'votes_add': 8, 'votes_subtract':2, 'votes': 6, 'postproc': 3},
            {'option': 'Option 3', 'number': 3, 'votes_add': 6, 'votes_subtract':1, 'votes': 5, 'postproc': 3},
            {'option': 'Option 2', 'number': 2, 'votes_add': 5, 'votes_subtract':2, 'votes': 3, 'postproc': 1},
            {'option': 'Option 5', 'number': 5, 'votes_add': 2, 'votes_subtract':0, 'votes': 2, 'postproc': 1},
            {'option': 'Option 1', 'number': 1, 'votes_add': 10, 'votes_subtract':12, 'votes': 0, 'postproc': 0},
        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)

        values = response.json()
        self.assertEqual(values, expected_result)


    def test_substrat_2(self):
        seats = 300
        data = {
            'seats': seats,
            'type': 'SUBTRAC',
            'options': [
                {'option': 'Option 1', 'number': 1, 'votes_add': 10032, 'votes_subtract':2345},
                {'option': 'Option 2', 'number': 2, 'votes_add': 423, 'votes_subtract':22},
                {'option': 'Option 3', 'number': 3, 'votes_add': 8002, 'votes_subtract':4231},
                {'option': 'Option 4', 'number': 4, 'votes_add': 1235, 'votes_subtract':1932},
                {'option': 'Option 5', 'number': 5, 'votes_add': 9012, 'votes_subtract':230},
                {'option': 'Option 6', 'number': 6, 'votes_add': 7000, 'votes_subtract': 4000},

            ]
        }

        expected_result = [
            {'option': 'Option 5', 'number': 5, 'votes_add': 9012, 'votes_subtract': 230, 'votes': 8782, 'postproc': 111},
            {'option': 'Option 1', 'number': 1, 'votes_add': 10032, 'votes_subtract': 2345, 'votes': 7687,'postproc': 98},
            {'option': 'Option 3', 'number': 3, 'votes_add': 8002, 'votes_subtract': 4231, 'votes': 3771,'postproc':48},
            {'option': 'Option 6', 'number': 6, 'votes_add': 7000, 'votes_subtract': 4000, 'votes': 3000,'postproc': 38},
            {'option': 'Option 2', 'number': 2, 'votes_add': 423, 'votes_subtract': 22, 'votes': 401, 'postproc': 5},
            {'option': 'Option 4', 'number': 4, 'votes_add': 1235, 'votes_subtract':1932, 'votes': 0, 'postproc': 0},
        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)

        values = response.json()
        self.assertEqual(values, expected_result)

    def test_substrat_no_options(self):
        seats = 300
        data = {
            'seats': seats,
            'type': 'SUBTRAC',

        }

        expected_result = {}

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 400)

        values = response.json()
        self.assertEqual(values, expected_result)


    def test_substrat_no_type(self):
        seats = 300
        data = {
            'seats': seats,
            'options': [
                {'option': 'Option 1', 'number': 1, 'votes_add': 10032, 'votes_subtract':2345},
                {'option': 'Option 2', 'number': 2, 'votes_add': 423, 'votes_subtract':22},
                {'option': 'Option 3', 'number': 3, 'votes_add': 8002, 'votes_subtract':4231},
                {'option': 'Option 4', 'number': 4, 'votes_add': 1235, 'votes_subtract':1932},
                {'option': 'Option 5', 'number': 5, 'votes_add': 9012, 'votes_subtract':230},
                {'option': 'Option 6', 'number': 6, 'votes_add': 7000, 'votes_subtract': 4000},

            ]
        }

        expected_result = {}

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 400)

        values = response.json()
        self.assertEqual(values, expected_result)

    def test_substrat_no_seats(self):
        data = {
            'type': 'SUBTRAC',
            'options': [
                {'option': 'Option 1', 'number': 1, 'votes_add': 10, 'votes_subtract':12},
                {'option': 'Option 2', 'number': 2, 'votes_add': 5, 'votes_subtract':2},
                {'option': 'Option 3', 'number': 3, 'votes_add': 6, 'votes_subtract':1},
                {'option': 'Option 4', 'number': 4, 'votes_add': 8, 'votes_subtract':2},
                {'option': 'Option 5', 'number': 5, 'votes_add': 2, 'votes_subtract':0},

            ]
        }

        expected_result = {}

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 400)

        values = response.json()
        self.assertEqual(values, expected_result)

    def test_hamilton_1(self):
        seats = 10
        data = {
            'type': 'HAMILTON',
            'seats': seats,
            'options': [
                {'option': 'Option 1', 'number': 1, 'votes': 15},
                {'option': 'Option 2', 'number': 2, 'votes': 3},
                {'option': 'Option 3', 'number': 3, 'votes': 12},
                {'option': 'Option 4', 'number': 4, 'votes': 0}
            ]
        }

        expected_result = [
            {'option': 'Option 1', 'number': 1, 'votes': 15, 'postproc': 5},
            {'option': 'Option 3', 'number': 3, 'votes': 12, 'postproc': 4},
            {'option': 'Option 2', 'number': 2, 'votes': 3, 'postproc': 1},
            {'option': 'Option 4', 'number': 4, 'votes': 0, 'postproc': 0}
        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)

        values = response.json()
        self.assertEqual(values, expected_result)

    def test_hamilton_2(self):
        seats = 9
        data = {
            'type': 'HAMILTON',
            'seats': seats,
            'options': [
                {'option': 'Option 1', 'number': 1, 'votes': 10},
                {'option': 'Option 2', 'number': 2, 'votes': 6},
                {'option': 'Option 3', 'number': 3, 'votes': 10},
                {'option': 'Option 4', 'number': 4, 'votes': 5},
                {'option': 'Option 5', 'number': 5, 'votes': 0}
            ]
        }

        expected_result = [
                {'option': 'Option 1', 'number': 1, 'votes': 10, 'postproc': 3},
                {'option': 'Option 3', 'number': 3, 'votes': 10, 'postproc': 3},
                {'option': 'Option 2', 'number': 2, 'votes': 6, 'postproc': 2},
                {'option': 'Option 4', 'number': 4, 'votes': 5, 'postproc': 1},
                {'option': 'Option 5', 'number': 5, 'votes': 0, 'postproc': 0}
        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)

        values = response.json()
        self.assertEqual(values, expected_result)
    
    # Test donde no se le pasa las variables options
    def test_no_options_hamilton(self):
        seats = 5
        data = {
            'type': 'HAMILTON',
            'seats': seats
        }
        expected_result = {}

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 400)

        values = response.json()
        self.assertEqual(values, expected_result)


    def test_no_seats_hamilton(self):
        data = {
            'type': 'HAMILTON',
            'options': [
                {'option': 'Option 1', 'number': 1, 'votes': 15},
                {'option': 'Option 2', 'number': 2, 'votes': 12},
                {'option': 'Option 3', 'number': 3, 'votes': 3},
                {'option': 'Option 4', 'number': 4, 'votes': 0}

            ]
        }
        expected_result = {}

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 400)

        values = response.json()
        self.assertEqual(values, expected_result)

    def test_no_type_hamilton(self):
        seats = 12
        data = {
            'seats': seats,
            'options': [
                {'option': 'Option 1', 'number': 1, 'votes': 15},
                {'option': 'Option 2', 'number': 2, 'votes': 12},
                {'option': 'Option 3', 'number': 3, 'votes': 3},
                {'option': 'Option 4', 'number': 4, 'votes': 0}
            ]
        }

        expected_result = {}

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 400)

        values = response.json()
        self.assertEqual(values, expected_result)
       
    def test_webster1(self):
        data = {
            'type': 'WEBSTER',
            'seats': 10,
            'options': [
                { 'option': 'Option 1', 'number': 1, 'votes': 10 },
                { 'option': 'Option 2', 'number': 2, 'votes': 0 },
                { 'option': 'Option 3', 'number': 3, 'votes': 7 },
                { 'option': 'Option 4', 'number': 4, 'votes': 2 },
                { 'option': 'Option 5', 'number': 5, 'votes': 5 },
                { 'option': 'Option 6', 'number': 6, 'votes': 1 },
            ]
        }
        expected_result = [
            { 'option': 'Option 1', 'number': 1, 'votes': 10, 'postproc': 4 },
            { 'option': 'Option 3', 'number': 3, 'votes': 7, 'postproc': 3 },
            { 'option': 'Option 5', 'number': 5, 'votes': 5, 'postproc': 2 },
            { 'option': 'Option 4', 'number': 4, 'votes': 2, 'postproc': 1 },
            { 'option': 'Option 6', 'number': 6, 'votes': 1, 'postproc': 0 },
            { 'option': 'Option 2', 'number': 2, 'votes': 0, 'postproc': 0 },
        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)

        values = response.json()
        self.assertEqual(values, expected_result)

    def test_webster2(self):
        data = {
            'type': 'WEBSTER',
            'seats': 12,
            'options': [
                { 'option': 'Option 1', 'number': 1, 'votes': 10 },
                { 'option': 'Option 2', 'number': 2, 'votes': 0 },
                { 'option': 'Option 3', 'number': 3, 'votes': 8 },
                { 'option': 'Option 4', 'number': 4, 'votes': 3 },
                { 'option': 'Option 5', 'number': 5, 'votes': 5 },
                { 'option': 'Option 6', 'number': 6, 'votes': 9 },
                { 'option': 'Option 7', 'number': 7, 'votes': 0 },
                { 'option': 'Option 8', 'number': 8, 'votes': 0 },
            ]
        }
        expected_result = [
            { 'option': 'Option 1', 'number': 1, 'votes': 10, 'postproc': 3 },
            { 'option': 'Option 6', 'number': 6, 'votes': 9, 'postproc': 3 },
            { 'option': 'Option 3', 'number': 3, 'votes': 8, 'postproc': 3 },
            { 'option': 'Option 5', 'number': 5, 'votes': 5, 'postproc': 2 },
            { 'option': 'Option 4', 'number': 4, 'votes': 3, 'postproc': 1 },
            { 'option': 'Option 2', 'number': 2, 'votes': 0, 'postproc': 0 },
            { 'option': 'Option 7', 'number': 7, 'votes': 0, 'postproc': 0 },
            { 'option': 'Option 8', 'number': 8, 'votes': 0, 'postproc': 0 },
        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)

        values = response.json()
        self.assertEqual(values, expected_result)


    #Test de algoritmo de webster con bastantes más datos y asientos
    def test_webster3(self):
        data = {
            'type': 'WEBSTER',
            'seats': 30,
            'options': [
                { 'option': 'Option 1', 'number': 1, 'votes': 31 },
                { 'option': 'Option 2', 'number': 2, 'votes': 19 },
                { 'option': 'Option 3', 'number': 3, 'votes': 8 },
                { 'option': 'Option 4', 'number': 4, 'votes': 3 },
                { 'option': 'Option 5', 'number': 5, 'votes': 5 },
                { 'option': 'Option 6', 'number': 6, 'votes': 9 },
                { 'option': 'Option 7', 'number': 7, 'votes': 4 },
                { 'option': 'Option 8', 'number': 8, 'votes': 0 },
                { 'option': 'Option 9', 'number': 1, 'votes': 15 },
                { 'option': 'Option 10', 'number': 2, 'votes': 6 },
                { 'option': 'Option 11', 'number': 3, 'votes': 9 },
                { 'option': 'Option 12', 'number': 4, 'votes': 19 },
                { 'option': 'Option 13', 'number': 5, 'votes': 16 },
                { 'option': 'Option 14', 'number': 6, 'votes': 6 },
                { 'option': 'Option 15', 'number': 7, 'votes': 0 },
            ]
        }
        expected_result = [
            { 'option': 'Option 1', 'number': 1, 'votes': 31, 'postproc': 6 } ,
            { 'option': 'Option 2', 'number': 2, 'votes': 19, 'postproc': 4 },
            { 'option': 'Option 12', 'number': 4, 'votes': 19, 'postproc': 4 },
            { 'option': 'Option 13', 'number': 5, 'votes': 16, 'postproc': 3 },
            { 'option': 'Option 9', 'number': 1, 'votes': 15, 'postproc': 3 },
            { 'option': 'Option 6', 'number': 6, 'votes': 9, 'postproc': 2 },
            { 'option': 'Option 11', 'number': 3, 'votes': 9, 'postproc': 2 },
            { 'option': 'Option 3', 'number': 3, 'votes': 8, 'postproc': 1 },
            { 'option': 'Option 10', 'number': 2, 'votes': 6, 'postproc': 1 },
            { 'option': 'Option 14', 'number': 6, 'votes': 6, 'postproc': 1 },
            { 'option': 'Option 5', 'number': 5, 'votes': 5, 'postproc': 1 },
            { 'option': 'Option 7', 'number': 7, 'votes': 4, 'postproc': 1 },
            { 'option': 'Option 4', 'number': 4, 'votes': 3, 'postproc': 1 },
            { 'option': 'Option 8', 'number': 8, 'votes': 0, 'postproc': 0 },
            { 'option': 'Option 15', 'number': 7, 'votes': 0, 'postproc': 0 }
                           ]


        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)

        values = response.json()
        print(values)
        self.assertEqual(values, expected_result)
        
    def test_paridad3(self):
        
        candidates1 = [{'name': 'Candidate1', 'gender': 'M'},
                       {'name': 'Candidate2', 'gender': 'M'},
                       {'name': 'Candidate3', 'gender': 'M'},
                       {'name': 'Candidate4', 'gender': 'M'},
                       {'name': 'Candidate5', 'gender': 'M'}]
        
        candidates2 = [{'name': 'Candidate6', 'gender': 'H'},
                       {'name': 'Candidate7', 'gender': 'H'},
                       {'name': 'Candidate8', 'gender': 'H'},
                       {'name': 'Candidate9', 'gender': 'H'},
                       {'name': 'Candidate10', 'gender': 'H'}]
        
        candidates3 = [{'name': 'Candidate11', 'gender': 'H'},
                       {'name': 'Candidate12', 'gender': 'M'},
                       {'name': 'Candidate13', 'gender': 'H'},
                       {'name': 'Candidate14', 'gender': 'M'},
                       {'name': 'Candidate15', 'gender': 'H'}]
        
        candidates4 = [{'name': 'Candidate16', 'gender': 'H'},
                       {'name': 'Candidate17', 'gender': 'H'},
                       {'name': 'Candidate18', 'gender': 'H'},
                       {'name': 'Candidate19', 'gender': 'M'},
                       {'name': 'Candidate20', 'gender': 'M'}]
        
        candidates5 = [{'name': 'Candidate21', 'gender': 'M'},
                       {'name': 'Candidate22', 'gender': 'M'},
                       {'name': 'Candidate23', 'gender': 'M'},
                       {'name': 'Candidate24', 'gender': 'H'},
                       {'name': 'Candidate25', 'gender': 'H'}]
        
    
        data = {
            'type': 'DHONT',
            'paridad': True,
            'seats': 20,
            'options': [
                { 'option': 'Option 1', 'number': 1, 'votes': 10, 'candidates': candidates1 },
                { 'option': 'Option 2', 'number': 2, 'votes': 10, 'candidates': candidates2 },
                { 'option': 'Option 3', 'number': 3, 'votes': 10, 'candidates': candidates3 },
                { 'option': 'Option 4', 'number': 4, 'votes': 10, 'candidates': candidates4 },
                { 'option': 'Option 5', 'number': 5, 'votes': 10, 'candidates': candidates5 },
            ]
        }
        
        seated1 = [{'name': 'Candidate1', 'gender': 'M'},
                       {'name': 'Candidate2', 'gender': 'M'},
                       {'name': 'Candidate3', 'gender': 'M'},
                       {'name': 'Candidate4', 'gender': 'M'},
                      ]
        
        seated2 = [{'name': 'Candidate6', 'gender': 'H'},
                       {'name': 'Candidate7', 'gender': 'H'},
                       {'name': 'Candidate8', 'gender': 'H'},
                       {'name': 'Candidate9', 'gender': 'H'},
                       ]
        
        seated3 = [{'name': 'Candidate11', 'gender': 'H'},
                       {'name': 'Candidate12', 'gender': 'M'},
                       {'name': 'Candidate13', 'gender': 'H'},
                       {'name': 'Candidate14', 'gender': 'M'},
                       ]
        
        seated4 = [{'name': 'Candidate16', 'gender': 'H'},
                       {'name': 'Candidate19', 'gender': 'M'},
                       {'name': 'Candidate17', 'gender': 'H'},     
                       {'name': 'Candidate20', 'gender': 'M'}]
        
        seated5 = [{'name': 'Candidate21', 'gender': 'M'},
                       {'name': 'Candidate24', 'gender': 'H'},
                       {'name': 'Candidate22', 'gender': 'M'},          
                       {'name': 'Candidate25', 'gender': 'H'}]

        expected_result = [
            { 'option': 'Option 1', 'number': 1, 'votes': 10, 'candidates': candidates1, 'postproc': 4, 'seated': seated1 },
            { 'option': 'Option 2', 'number': 2, 'votes': 10, 'candidates': candidates2 , 'postproc': 4, 'seated': seated2  },
            { 'option': 'Option 3', 'number': 3, 'votes': 10, 'candidates': candidates3, 'postproc': 4, 'seated': seated3  },
            { 'option': 'Option 4', 'number': 4, 'votes': 10, 'candidates': candidates4, 'postproc': 4, 'seated': seated4},
            { 'option': 'Option 5', 'number': 5, 'votes': 10, 'candidates': candidates5 , 'postproc': 4, 'seated': seated5},
            
          ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)
        values = response.json()
        self.assertEqual(values, expected_result)
    
    
    def test_no_options_webster(self):
        seats = 10
        data = {
            'type': 'WEBSTER    ',
            'seats': seats
        }
        expected_result = {}

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 400)

        values = response.json()
        self.assertEqual(values, expected_result)

    #Test en el que no se le pasan seats al algoritmo de webster
    def test_webster_no_seats(self):
        data = {
            'type': 'WEBSTER',
            'options': [
                { 'option': 'Option 1', 'number': 1, 'votes': 12 },
                { 'option': 'Option 2', 'number': 2, 'votes': 3 },
                { 'option': 'Option 3', 'number': 3, 'votes': 8 },
                { 'option': 'Option 4', 'number': 4, 'votes': 3 },
                { 'option': 'Option 5', 'number': 5, 'votes': 5 },
                { 'option': 'Option 6', 'number': 6, 'votes': 9 },
                { 'option': 'Option 7', 'number': 7, 'votes': 0 },
                { 'option': 'Option 8', 'number': 8, 'votes': 0 },
                { 'option': 'Option 9', 'number': 9, 'votes': 5 },
                { 'option': 'Option 10', 'number': 10, 'votes': 6} ,
            ]
        }

        expected_result = {}

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 400)

        values = response.json()
        self.assertEqual(values, expected_result)


    #Test en el que no se le pasa tipo
    def test_webster_no_type(self):
        data = {
            'seats': 5,
            'options': [
                { 'option': 'Option 1', 'number': 1, 'votes': 12 },
                { 'option': 'Option 2', 'number': 2, 'votes': 3 },
                { 'option': 'Option 3', 'number': 3, 'votes': 8 },
                { 'option': 'Option 4', 'number': 4, 'votes': 3 },
                { 'option': 'Option 5', 'number': 5, 'votes': 5 },
                { 'option': 'Option 6', 'number': 6, 'votes': 9 },
                { 'option': 'Option 7', 'number': 7, 'votes': 0 },
                { 'option': 'Option 8', 'number': 8, 'votes': 0 },
                { 'option': 'Option 9', 'number': 9, 'votes': 5 },
                { 'option': 'Option 10', 'number': 10, 'votes': 6} ,
            ]
        }

        expected_result = {}

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 400)

        values = response.json()
        self.assertEqual(values, expected_result)

    def test_webster_modificado_1(self):
            data = {
                'type': 'WEBSTERMOD',
                'seats': 8,
                'options': [
                    { 'option': 'Option 1', 'number': 1, 'votes': 10 },
                    { 'option': 'Option 2', 'number': 2, 'votes': 0 },
                    { 'option': 'Option 3', 'number': 3, 'votes': 7 },
                    { 'option': 'Option 4', 'number': 4, 'votes': 5 },
                ]
            }
            expected_result = [
                { 'option': 'Option 1', 'number': 1, 'votes': 10, 'postproc': 4 },
                { 'option': 'Option 3', 'number': 3, 'votes': 7, 'postproc': 2 },
                { 'option': 'Option 4', 'number': 4, 'votes': 5, 'postproc': 2 },
                { 'option': 'Option 2', 'number': 2, 'votes': 0, 'postproc': 0 },
            ]

            response = self.client.post('/postproc/', data, format='json')
            self.assertEqual(response.status_code, 200)

            values = response.json()
            self.assertEqual(values, expected_result)

    def test_no_options_webter_modificado(self):
            seats = 5
            data = {
                'type': 'WEBSTERMOD',
                'seats': seats
            }
            expected_result = {}

            response = self.client.post('/postproc/', data, format='json')
            self.assertEqual(response.status_code, 400)

            values = response.json()
            self.assertEqual(values, expected_result)
