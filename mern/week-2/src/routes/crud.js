const express = require('express');
const mongoose = require('mongoose');

/**
 * Builds a CRUD router for a model whose documents belong to the signed-in user.
 * `pick` lists the fields a client may set, so owner and other fields cannot be overwritten.
 */
module.exports = function crudRouter(Model, pick) {
  const router = express.Router();
  const clean = body => Object.fromEntries(pick.filter(k => body && body[k] !== undefined).map(k => [k, body[k]]));
  const validId = (req, res, next) => (mongoose.isValidObjectId(req.params.id) ? next() : res.status(400).json({ error: 'Invalid id' }));

  router.get('/', async (req, res, next) => {
    try {
      res.json(await Model.find({ owner: req.userId }).sort({ createdAt: -1 }));
    } catch (err) {
      next(err);
    }
  });

  router.post('/', async (req, res, next) => {
    try {
      res.status(201).json(await Model.create({ ...clean(req.body), owner: req.userId }));
    } catch (err) {
      next(err);
    }
  });

  router.get('/:id', validId, async (req, res, next) => {
    try {
      const doc = await Model.findOne({ _id: req.params.id, owner: req.userId });
      doc ? res.json(doc) : res.status(404).json({ error: 'Not found' });
    } catch (err) {
      next(err);
    }
  });

  router.put('/:id', validId, async (req, res, next) => {
    try {
      const doc = await Model.findOneAndUpdate({ _id: req.params.id, owner: req.userId }, clean(req.body), { returnDocument: 'after', runValidators: true });
      doc ? res.json(doc) : res.status(404).json({ error: 'Not found' });
    } catch (err) {
      next(err);
    }
  });

  router.delete('/:id', validId, async (req, res, next) => {
    try {
      const doc = await Model.findOneAndDelete({ _id: req.params.id, owner: req.userId });
      doc ? res.status(204).end() : res.status(404).json({ error: 'Not found' });
    } catch (err) {
      next(err);
    }
  });

  return router;
};
