const jwt = require("jsonwebtoken");
const bcryptjs = require("bcryptjs");
const express = require("express");

const router = express.Router();
const { ensureGuest } = require("../middleware/auth");
const User = require("../models/userModel");

const createToken = (res, req, user) => {
  const token = jwt.sign(
    { username: user.username, role: user.role, _id: user._id },
    process.env.SECRET,
    {
      expiresIn: "3d",
    }
  );
  res.cookie("cookieToken", token, { httpOnly: true });
  req.user = user;
  user.role === "patient" ? res.redirect("/home") : res.redirect("/staff");
};

// @desc    Login page
// @route   GET /
router.get("/login", ensureGuest, (req, res) => {
  res.render("login", {
    layout: "auth",
  });
});

// @desc    Login page
// @route   POST /auth/login
router.post("/login", async (req, res, next) => {
  const { email, password } = req.body;

  try {
    const user = await User.login(email, password);
    createToken(res, req, user);
  } catch (error) {
    //res.send( `<p>${error.message}</p><p>Error. <a href="/">Go back home.</a></p>`);
    res.render("error/virhe");
  }
});

// @desc    logout user
// @route   GET /auth/logout
router.get("/logout", (req, res) => {
  res.clearCookie("cookieToken");
  res.redirect("/");
});

// @desc    register page
// @route   GET /register
router.get("/register", ensureGuest, (req, res) => {
  res.render("signup", {
    layout: "auth",
  });
});

// @desc    Register page
// @route   POST /auth/register
router.post("/register", async (req, res, next) => {
  const { username, email, password, role } = req.body;

  try {
    const user = await User.signup(username, email, password, role);

    createToken(res, req, user);
  } catch (error) {
    console.log(error);
    //res.send(`<p>Error: ${error} <a href="/">Go back home.</a></p>`);
    res.render("error/virhe");
  }
});

module.exports = router;
