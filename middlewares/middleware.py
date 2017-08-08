# coding=utf-8
from __future__ import absolute_import

import cProfile
import logging
import pstats
from StringIO import StringIO

from django.conf import settings
from django.http import HttpResponse

LOG = logging.getLogger(__name__)


class OwnPyProfileMiddleware(object):
    """
    请求耗时可视化中间件.
    """

    @classmethod
    def can(cls, request):
        full_path = request.get_full_path()
        return settings.DEBUG and "?profile" in full_path

    def process_view(self, request, callback, callback_args, callback_kwargs):
        setattr(self, 'profiler', cProfile.Profile())
        LOG.info("Going to profiling {}".format(callback.__name__))
        self.profiler.runcall(callback, request, *callback_args, **callback_kwargs)

    def process_response(self, request, response):
        if self.can(request):
            self.profiler.create_stats()
            params = request.GET.copy()

            sort_param = params.get('sort', 'cumulative')
            amount = params.get('count', 200)
            if 'download' in params:
                import marshal
                output = marshal.dumps(self.profiler.stats)
                response = HttpResponse(output, content_type='application/octet-stream')
                response['Content-Disposition'] = 'attachment; filename=view.prof'
                response['Content-Length'] = len(output)
            else:
                io = StringIO()
                stats = pstats.Stats(self.profiler, stream=io)
                stats.sort_stats(sort_param)
                if amount:
                    stats.print_stats(int(amount))
                else:
                    stats.print_stats()
                # print io.getvalue()  # debug
                response = HttpResponse('<pre>\n%s\n</pre>' % io.getvalue())
        return response
