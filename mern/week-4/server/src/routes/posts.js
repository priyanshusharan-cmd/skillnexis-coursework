const express = require('express');
const mongoose = require('mongoose');
const Post = require('../models/Post');

/** Shapes a post for the client for a given viewer. */
function present(post, viewerId) {
  const author = post.author && post.author.name ? { id: post.author.id, name: post.author.name } : { id: String(post.author), name: 'Unknown' };
  return {
    id: post.id,
    text: post.text,
    author,
    createdAt: post.createdAt,
    likeCount: post.likes.length,
    likedByMe: post.likes.some(id => String(id) === viewerId),
    comments: post.comments.map(c => ({ id: c.id, text: c.text, createdAt: c.createdAt, author: c.author && c.author.name ? { id: c.author.id, name: c.author.name } : { id: String(c.author), name: 'Unknown' } })),
  };
}

module.exports = function postRoutes() {
  const router = express.Router();
  const load = id => Post.findById(id).populate('author', 'name').populate('comments.author', 'name');
  const validId = (req, res, next) => (mongoose.isValidObjectId(req.params.id) ? next() : res.status(400).json({ error: 'Invalid id' }));

  router.get('/', async (req, res, next) => {
    try {
      const limit = Math.min(Number.parseInt(req.query.limit, 10) || 20, 50);
      const filter = req.query.before && mongoose.isValidObjectId(req.query.before) ? { _id: { $lt: req.query.before } } : {};
      const posts = await Post.find(filter).sort({ _id: -1 }).limit(limit).populate('author', 'name').populate('comments.author', 'name');
      res.json(posts.map(p => present(p, req.userId)));
    } catch (err) {
      next(err);
    }
  });

  router.post('/', async (req, res, next) => {
    try {
      const text = req.body && typeof req.body.text === 'string' ? req.body.text.trim() : '';
      if (!text) return res.status(400).json({ error: 'Write something first' });
      if (text.length > 500) return res.status(400).json({ error: 'Posts are limited to 500 characters' });
      const post = await Post.create({ author: req.userId, text });
      res.status(201).json(present(await load(post.id), req.userId));
    } catch (err) {
      next(err);
    }
  });

  // Toggle: liking twice removes the like, and one user can only like a post once.
  router.post('/:id/like', validId, async (req, res, next) => {
    try {
      const post = await Post.findById(req.params.id);
      if (!post) return res.status(404).json({ error: 'Post not found' });
      const liked = post.likes.some(id => String(id) === req.userId);
      await Post.updateOne({ _id: post._id }, liked ? { $pull: { likes: req.userId } } : { $addToSet: { likes: req.userId } });
      res.json(present(await load(post.id), req.userId));
    } catch (err) {
      next(err);
    }
  });

  router.post('/:id/comments', validId, async (req, res, next) => {
    try {
      const text = req.body && typeof req.body.text === 'string' ? req.body.text.trim() : '';
      if (!text) return res.status(400).json({ error: 'Write a comment first' });
      if (text.length > 300) return res.status(400).json({ error: 'Comments are limited to 300 characters' });
      const updated = await Post.findByIdAndUpdate(req.params.id, { $push: { comments: { author: req.userId, text } } });
      if (!updated) return res.status(404).json({ error: 'Post not found' });
      res.status(201).json(present(await load(req.params.id), req.userId));
    } catch (err) {
      next(err);
    }
  });

  router.delete('/:id', validId, async (req, res, next) => {
    try {
      const post = await Post.findById(req.params.id);
      if (!post) return res.status(404).json({ error: 'Post not found' });
      if (String(post.author) !== req.userId) return res.status(403).json({ error: 'You can only delete your own posts' });
      await post.deleteOne();
      res.status(204).end();
    } catch (err) {
      next(err);
    }
  });

  return router;
};
