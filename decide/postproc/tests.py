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
                {'option': 'Option 3', 'number': 3, 'votes': 0},

            ],
            'order_options': []
        }

        expected_result = {}

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 400)

        values = response.json()
        self.assertEqual(values, expected_result)