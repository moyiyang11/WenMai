"""数据库引擎与会话。MVP 使用 SQLite。"""
from collections.abc import Generator

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from core.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args, future=True)


# SQLite 默认不开启外键约束，导致 CASCADE DELETE 失效。每次拿到连接时强制开启。
if settings.database_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_sqlite_fk(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 轻量自动补列：仅新增列，覆盖 SQLite 下老库无法被 create_all 补列的场景。
# 结构复杂的变更仍应交由正式迁移工具（如 Alembic）。
_ADDED_COLUMNS: dict[str, dict[str, str]] = {
    "style_features": {"origin": "VARCHAR(16) DEFAULT ''"},
}


def _automigrate() -> None:
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    with engine.begin() as conn:
        for table, columns in _ADDED_COLUMNS.items():
            if table not in existing_tables:
                continue
            have = {c["name"] for c in inspector.get_columns(table)}
            for col, ddl in columns.items():
                if col not in have:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}"))


def init_db() -> None:
    """建表。导入 models 以注册所有映射。"""
    import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _automigrate()
