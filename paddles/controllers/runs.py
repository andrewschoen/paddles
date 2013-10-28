from pecan import conf, expose, redirect, request
from paddles.models import Run
from paddles.controllers.jobs import JobsController
from paddles.controllers import error


def latest_runs(count, fields=None):
    runs = Run.query.order_by(Run.posted.desc()).limit(count).all()
    if fields:
        try:
            return dict(latest_runs=[run.slice(fields) for run in runs])
        except AttributeError:
            error('/errors/invalid/',
                  'an invalid field was specified')
    return dict(
        latest_runs=[run for run in runs]
    )


class RunController(object):

    def __init__(self, name):
        self.name = name
        try:
            self.run = Run.filter_by(name=name).first()
        except ValueError:
            self.run = None
        request.context['run'] = self.run
        request.context['run_name'] = self.name

    @expose(generic=True, template='json')
    def index(self):
        if not self.run:
            error('/errors/not_found/',
                  'requested run resource does not exist')
        json_run = self.run.__json__()
        json_run['jobs'] = self.run.get_jobs()
        return json_run

    @index.when(method='DELETE', template='json')
    def index_delete(self):
        if not self.run:
            error('/errors/not_found/',
                  'attempted to delete a non-existent run')
        self.run.delete()
        return dict()

    jobs = JobsController()


class LatestRunsByCountController(object):

    def __init__(self, count):
        if count == '':
            count = conf.default_latest_runs_count

        try:
            self.count = int(count)
        except ValueError:
            error('/errors/invalid/',
                  "must specify an integer")

    @expose('json')
    def index(self, fields=''):
        return latest_runs(self.count, fields)


class LatestRunsController(object):

    @expose(generic=True, template='json')
    def index(self, fields=''):
        count = conf.default_latest_runs_count
        return latest_runs(count, fields)

    @expose('json')
    def _lookup(self, count, *remainder):
        return LatestRunsByCountController(count), remainder


class RunsController(object):

    @expose(generic=True, template='json')
    def index(self, fields=''):
        return latest_runs(conf.default_latest_runs_count, fields)

    @index.when(method='POST', template='json')
    def index_post(self):
        # save to DB here
        try:
            name = request.json.get('name')
        except ValueError:
            error('/errors/invalid/', 'could not decode JSON body')
        if not name:
            error('/errors/invalid/', "could not find required key: 'name'")
        if not Run.filter_by(name=name).first():
            new_run = Run(name)
            return dict()
        else:
            error('/errors/invalid/', "run with name %s already exists" % name)

    latest = LatestRunsController()

    @expose('json')
    def _lookup(self, name, *remainder):
        return RunController(name), remainder
