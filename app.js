require("dotenv").config();

const express = require("express");
const mongoose = require("mongoose");
const cors = require("cors");
const { engine } = require("express-handlebars");
const path = require("path");
const morgan = require("morgan");

const cookieParser = require("cookie-parser");
const favicon = require("serve-favicon");
const methodOverride = require("method-override");
const workoutRoutes = require("./routes/api/workouts");
const userRoutes = require("./routes/user");

mongoose.set("strictQuery", true);
// express app
const app = express();

// middleware

app.use(express.urlencoded({ extended: false }));
app.use(express.json());
app.use(cookieParser());

app.use(cors());
app.use(favicon(path.join(__dirname, "public", "favicon.ico")));

app.use((req, res, next) => {
  console.log(req.path, req.method);
  next();
});

// Method override
app.use(
  methodOverride(function (req, res) {
    if (req.body && typeof req.body === "object" && "_method" in req.body) {
      // look in urlencoded POST bodies and delete it
      let method = req.body._method;
      delete req.body._method;
      return method;
    }
  })
);

// Logging
if (process.env.NODE_ENV === "development") {
  app.use(morgan("dev"));
}

const options = {
  layoutsDir: "views/layouts/",
  defaultLayout: "main",
  partialsDir: "views/partials/",
  helpers: require("./helpers/hbs"),
  extname: ".hbs",
};

app.engine(".hbs", engine(options));
app.set("view engine", ".hbs");
app.set("views", "./views");

// Static folder
app.use(express.static(path.join(__dirname, "public")));

// routes

app.use("/", require("./routes/index"));
app.use("/auth", require("./routes/auth"));
app.use("/stories", require("./routes/stories"));
app.use("/api/workouts", require("./routes/api/workouts"));
app.use("/api/user", require("./routes/user"));
app.use("/kubios", require("./routes/kubios"));

// connect to db
mongoose
  .connect(process.env.MONGO_URI)
  .then(() => {
    console.log("connected to database");
    // listen to port
    app.listen(process.env.PORT, () => {
      console.log("listening for requests on port", process.env.PORT || 3000);
    });
  })
  .catch((err) => {
    console.log(err);
  });
