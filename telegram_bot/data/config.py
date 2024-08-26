from environs import Env
# from google.oauth2.service_account import Credentials
# from sqlalchemy import create_engine

env = Env()
env.read_env()

BOT_TOKEN = env.str("BOT_TOKEN")  # Забираем значение типа str
OWNERS = env.list("OWNERS")
# print(OWNERS)
ADMINS = env.list("ADMINS") + OWNERS  # Тут у нас будет список из админов
CRM_ADMINS = env.list("ADMINS") + OWNERS
# print(ADMINS)
IP = env.str("ip")  # Тоже str, но для айпи адреса хоста

# PGUSER = env.str("DB_USER")
# PGPASS = env.str("DB_PASS")
# PGNAME = env.str("DB_NAME")
# PGHOST = env.str("DB_HOST")
# PGPORT = env.str("DB_PORT")
# DATABASE = env.str("DATABASE")
#
# LIQPAY_TOKEN = env.str("LIQPAY")


def get_scoped_credentials(credentials, scopes):
    def prepare_credentials():
        return credentials.with_scopes(scopes)


# GOOGLE_API_KEY = env.str("GOOGLE_API_KEY")
# google_credentials: Credentials = Credentials.from_service_account_file('huhy-club-23fec1ac9059.json')
# scopes = [
#     "https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
#     "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"
# ]
# scoped_credentials = get_scoped_credentials(google_credentials, scopes)

# db_host = ip

# aiogram_redis = {
#     'host': ip,
# }
#
# redis = {
#     'address': (ip, 6379),
#     'encoding': 'utf8'
# }


# engine = create_engine(
#     f"postgresql://{PGUSER}:{PGPASS}@{PGHOST}:{PGPORT}/{PGNAME}",
#     connect_args={'client_encoding': 'utf8'}
# )
#
# conn = engine.connect()
#
# POSTGRES_URI = f"postgresql://{PGUSER}:{PGPASS}@{PGHOST}:{PGPORT}/{PGNAME}"
# TIMEZONE_BASE_URL = "https://maps.googleapis.com/maps/api/timezone/json"
