from google_auth_oauthlib.flow import Flow
GOOGLE_CLIENT_ID = "645826919583-t9v4loh04drq6npdtq3t4g25bcdd7ju1.apps.googleusercontent.com"
client_secrets_file=os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

flow = Flow.from_client_secrets_file(
  client_secrets_file=client_secrets_file, 
scopes=["https://www.googleapis.com/auth/userinfo.profile","https://www.googleapis.com/auth/userinfo.email","openid"],
  redirect_uri="https://Competitive-Cycling-Website.arnavkumar13.repl.co/callback" 
)
def login():
  authorization_url, state=flow.authorization_url(
  session["state"]=state
  return redirect(authorization_url)
  