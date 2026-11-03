-- Social media app schema, normalised to 3NF (see social-media-schema.md).
-- Written for PostgreSQL. schema_check.py loads a SQLite-compatible copy and runs the example queries.

CREATE TABLE users (
  id            BIGSERIAL PRIMARY KEY,
  username      VARCHAR(30)  NOT NULL UNIQUE,
  email         VARCHAR(254) NOT NULL UNIQUE,
  password_hash TEXT         NOT NULL,
  display_name  VARCHAR(60)  NOT NULL,
  bio           VARCHAR(300),
  created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- Self-referencing many-to-many: who follows whom.
CREATE TABLE follows (
  follower_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  followee_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (follower_id, followee_id),
  CHECK (follower_id <> followee_id)
);
CREATE INDEX idx_follows_followee ON follows(followee_id);   -- "who follows me"

CREATE TABLE posts (
  id         BIGSERIAL PRIMARY KEY,
  author_id  BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  body       VARCHAR(2000) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_posts_author_time ON posts(author_id, created_at DESC);  -- profile pages and the feed

-- A post has 0..n media items; kept separate so posts stay 1NF (no list of URLs in one column).
CREATE TABLE media (
  id        BIGSERIAL PRIMARY KEY,
  post_id   BIGINT NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
  kind      VARCHAR(10) NOT NULL CHECK (kind IN ('image', 'video')),
  url       TEXT NOT NULL,
  position  SMALLINT NOT NULL,
  UNIQUE (post_id, position)
);

CREATE TABLE comments (
  id         BIGSERIAL PRIMARY KEY,
  post_id    BIGINT NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
  author_id  BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  parent_id  BIGINT REFERENCES comments(id) ON DELETE CASCADE,  -- replies
  body       VARCHAR(1000) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_comments_post ON comments(post_id, created_at);

CREATE TABLE post_likes (
  post_id    BIGINT NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
  user_id    BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (post_id, user_id)                -- one like per user per post
);
CREATE INDEX idx_post_likes_user ON post_likes(user_id);

-- Hashtags: many-to-many between posts and tags.
CREATE TABLE hashtags (
  id  BIGSERIAL PRIMARY KEY,
  tag VARCHAR(50) NOT NULL UNIQUE               -- stored lower-case
);
CREATE TABLE post_hashtags (
  post_id    BIGINT NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
  hashtag_id BIGINT NOT NULL REFERENCES hashtags(id) ON DELETE CASCADE,
  PRIMARY KEY (post_id, hashtag_id)
);
CREATE INDEX idx_post_hashtags_tag ON post_hashtags(hashtag_id);

-- Direct messages between two users.
CREATE TABLE conversations (
  id         BIGSERIAL PRIMARY KEY,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE conversation_members (
  conversation_id BIGINT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  user_id         BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  PRIMARY KEY (conversation_id, user_id)
);
CREATE TABLE messages (
  id              BIGSERIAL PRIMARY KEY,
  conversation_id BIGINT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  sender_id       BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  body            VARCHAR(2000) NOT NULL,
  sent_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_messages_conv_time ON messages(conversation_id, sent_at);

CREATE TABLE notifications (
  id         BIGSERIAL PRIMARY KEY,
  user_id    BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,  -- recipient
  actor_id   BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  type       VARCHAR(20) NOT NULL CHECK (type IN ('like', 'comment', 'follow', 'mention')),
  post_id    BIGINT REFERENCES posts(id) ON DELETE CASCADE,
  read_at    TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_notifications_unread ON notifications(user_id, created_at DESC) WHERE read_at IS NULL;
