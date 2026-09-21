from sqlmodel import create_engine, Session
from backend.core.config import settings

# Managed Postgres providers (Railway/Neon/Render) drop idle TCP connections
# behind their proxies. Without pool_pre_ping the pool hands out those dead
# sockets and requests fail with "SSL connection has been closed unexpectedly".
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    echo=settings.sql_echo,
    pool_pre_ping=True,      # test liveness before each checkout; reconnect if dead
    pool_recycle=240,        # proactively retire connections older than 4 min
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    connect_args={
        "connect_timeout": 10,
        "application_name": "actuator-ai",
        # libpq TCP keepalives: detect half-open connections within ~60s
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    },
)

def get_session():
    with Session(engine) as session:
        yield session
