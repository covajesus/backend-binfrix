-- Migración: tabla blog_posts (sitio corporativo)
-- Uso:
--   python scripts/migrate_blog_posts.py
--   mysql -u ... -p binfrix < scripts/migrate_blog_posts.sql

CREATE TABLE IF NOT EXISTS blog_posts (
  id VARCHAR(36) NOT NULL,
  slug VARCHAR(120) NOT NULL,
  title VARCHAR(255) NOT NULL,
  type VARCHAR(80) NOT NULL DEFAULT 'Artículo',
  published_at DATE NOT NULL,
  read_time VARCHAR(40) NOT NULL DEFAULT '',
  excerpt TEXT NOT NULL,
  cover_image_url TEXT NOT NULL,
  sections JSON NOT NULL,
  related_slugs JSON NOT NULL,
  sort_order INTEGER NOT NULL DEFAULT 0,
  status VARCHAR(20) NOT NULL DEFAULT 'published',
  created_at DATETIME(6) NOT NULL,
  updated_at DATETIME(6) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_blog_posts_slug (slug),
  KEY ix_blog_posts_slug (slug),
  KEY ix_blog_posts_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
