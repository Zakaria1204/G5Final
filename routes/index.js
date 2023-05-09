const express = require('express');
const router = express.Router();
const jwt = require('jsonwebtoken');
const { authorize, ensureAuth, ensureGuest } = require('../middleware/auth');

// @desc    about/Landing page
// @route   GET /
router.get('/', ensureGuest, (req, res) => {
  res.render('home', {
    layout: 'auth',
  });
});

// @desc    about/Landing page
// @route   GET /home
router.get('/home', ensureAuth, authorize('patient'), (req, res) => {
  res.render('home-patient', {
    username: req.user.username,
    role: req.user.role,
  });
});

// @desc    appointment page
// @route   GET /appointment
router.get('/appointment', ensureAuth, authorize('patient'), (req, res) => {
  res.render('appointment');
});

// @desc    doctors page
// @route   GET /doctors
router.get('/staff', ensureAuth, authorize('doctor', 'nurse'), (req, res) => {
  res.render('staff', {
    layout: 'staff',
  });
});

// @desc    doctors page
// @route   GET /patients
router.get(
  '/patients',
  ensureAuth,
  authorize('doctor', 'nurse'),
  (req, res) => {
    res.render('patients', {
      layout: 'staff',
    });
  }
);

// @desc    contact page
// @route   GET /contact
router.get('/contact', (req, res) => {
  res.render('contact', {
    layout: 'simple',
  });
});

// @desc    faq page
// @route   GET /faq
router.get('/faq', ensureAuth, authorize('patient'), (req, res) => {
  res.render('faq');
});

// @desc    why page
// @route   GET /
router.get('/why', ensureAuth, authorize('patient'), (req, res) => {
  res.render('why');
});

module.exports = router;
