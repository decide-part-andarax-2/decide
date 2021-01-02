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

           