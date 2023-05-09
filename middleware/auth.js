const jwt = require('jsonwebtoken');
const ErrorResponse = require('../helpers/errorResponse');
module.exports = {
  ensureAuth: function (req, res, next) {
    jwt.verify(
      req.cookies.cookieToken,
      process.env.SECRET,
      function (err, decoded) {
        if (err) {
          res.redirect('/auth/login');
        } else {
          req.user = decoded;
          next();
        }
      }
    );
  },
  ensureGuest: function (req, res, next) {
    jwt.verify(
      req.cookies.cookieToken,
      process.env.SECRET,
      function (err, decoded) {
        if (err) {
          next();
        } else {
          res.redirect('/');
        }
      }
    );
  },
  authorize: function (...roles) {
    return (req, res, next) => {
      if (!roles.includes(req.user.role)) {
        return next(
          new ErrorResponse(
            `User role ${req.user.role} is not authorized to access this route`,
            403
          )
        );
      }
      next();
    };
  },
};
