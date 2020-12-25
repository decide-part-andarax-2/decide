from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response


class PostProcView(APIView):

    def identity(self, options):
        out = []

        for opt in options:
            out.append({
                **opt,
                'postproc': opt['votes'],
            });

        out.sort(key=lambda x: -x['postproc'])
        return Response(out)

    def relativa(self, options):
        out= []
        numvotos=0

        for opt in options:
            numvotos=opt['votes']+numvotos
            out.append({
                **opt,
                'postproc':0,
            })

        mayor=0.0
        while len(out)>=2:

            if len(out)>2:
                cocientes = []
                for i in range(len(out)):
                   cocientes.append(out[i]['votes']/numvotos)       
                perdedor=cocientes.index(min(cocientes))
                ganador=cocientes.index(max(cocientes))
                mayor=cocientes[ganador]
                if mayor>0.5:
                    out[ganador]['postproc']= 1
                    break
                numvotos= numvotos - cocientes[perdedor]
                del out[perdedor]
            elif len(out)==2:
                cocientes = []
                for i in range(len(out)):
                    cocientes.append(out[i]['votes']/numvotos)
                ganador=cocientes.index(max(cocientes))  
                out[ganador]['postproc']= 1
                break

        out.sort(key=lambda x:-x['votes'])
        return Response(out)

    def absoluta(self, options):
        out= []
        numvotos=0

        for opt in options:
            numvotos=opt['votes']+numvotos
            out.append({
                **opt,
                'postproc':0,
            })

        if len(out)>=2:
            cocientes = []
            for i in range(len(out)):
                cocientes.append(out[i]['votes']/numvotos)
            ganador=cocientes.index(max(cocientes))
            mayor=cocientes[ganador]

            if mayor>0.5:
                out[ganador]['postproc']= 1
        else:
            out[0]['postproc']= 1
                
        out.sort(key=lambda x:-x['votes'])
        return Response(out)

    def dhont(self, options, seats):
        out = []

        for opt in options:
            out.append({
                **opt,
                'postproc': 0,
            });

        asientos = 0
        while asientos < seats:
            cocientes = []
            for i in range(len(out)):
                cocientes.append(out[i]['votes'] / (out[i]['postproc'] + 1))

            ganador = cocientes.index(max(cocientes))
            out[ganador]['postproc'] = out[ganador]['postproc'] + 1
            asientos += 1

        out.sort(key=lambda x: -x['votes'])
        return Response(out)

    def post(self, request):
        """
         * type: IDENTITY | DHONT | RELATIVA | ABSOLUTA
         * options: [
            {
             option: str,
             number: int,
             votes: int,
             ...extraparams
            }
           ]
	    * seats: int
        """

        t = request.data.get('type')
        opts = request.data.get('options', [])
        s = request.data.get('seats')

        if len(opts) == 0:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)

        if t == 'IDENTITY':
            return self.identity(opts)
        elif t == 'RELATIVA':
            return self.relativa(opts)
        elif t == 'ABSOLUTA':
            return self.absoluta(opts)
        elif t == 'DHONT':
            if(s==None):
                return Response({}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return self.dhont(opts, s)
        else:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)
        return Response({})
