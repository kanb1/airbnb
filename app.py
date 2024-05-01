#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

#https://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@github.com/kanb1/airbnb.git

#########################
from bottle import default_app, get, post, run
import git
 
@post('/secret_url_for_git_hook')
def git_update():
  repo = git.Repo('./airbnb')
  origin = repo.remotes.origin
  repo.create_head('main', origin.refs.main).set_tracking_branch(origin.refs.main).checkout()
  origin.pull()
  return ""
 
 
##############################
@get("/")
def _():
  return "Three"
 
##############################
try:
  import production
  application = default_app()
except Exception as ex:
  print("Running local server")
  run(host="127.0.0.1", port=80, debug=True, reloader=True)