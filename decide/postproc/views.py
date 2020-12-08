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

    def dhont(self, options, seats):
        out = []

        for opt in options:
            out.append({
                **opt,
                'postproc': opt['votes'],
            });

        asientos = 0
        while asientos <= seats:
            cocientes = []
            for i in range(len(out)):
                cocientes.append(out[i]['votes'] / out[i]['postproc'] + 1)

                ganador = cocientes.index(max(cocientes))
                out[ganador]['postproc'] = out[ganador]['postproc'] + 1
                asientos += 1

        out.sort(key=lambda x: -x['postproc'])
        return Response(out)

    def post(self, request):
        """
         * type: IDENTITY | DHONT
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

        if t == 'IDENTITY':
            return self.identity(opts)

        elif t == 'DHONT':
            return self.dhont(opts, s)

        return Response({})
