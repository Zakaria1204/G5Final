// const fetch = require("node-fetch-commonjs");
const fetch = require('node-fetch');
const { v4 } = require("uuid");

const csrf = v4();
const USER_AGENT = "TestApp 1.0";
const LOGIN_URL = "https://kubioscloud.auth.eu-west-1.amazoncognito.com/login";
const TOKEN_URL =
  "https://kubioscloud.auth.eu-west-1.amazoncognito.com/oauth2/token";
const REDIRECT_URI = "https://analysis.kubioscloud.com/v1/portal/login";

const user_login = async (username, password, client_id) => {
  const headers = new Headers();
  headers.append("Cookie", `XSRF-TOKEN=${csrf}`);
  headers.append("User-Agent", USER_AGENT);

  const searchParams = new URLSearchParams();
  searchParams.set("username", username);
  searchParams.set("password", password);
  searchParams.set("client_id", client_id);
  searchParams.set("redirect_uri", REDIRECT_URI);
  searchParams.set("response_type", "token");
  searchParams.set("scope", "openid");
  searchParams.set("_csrf", csrf);

  const options = {
    method: "POST",
    headers: headers,
    redirect: "manual",
    body: searchParams,
  };

  const response = await fetch(LOGIN_URL, options);
  const location = response.headers.raw().location[0];

  const regex = /id_token=(.*)&access_token=(.*)&expires_in=(.*)/;
  const match = location.match(regex);

  const tokens = {
    id_token: match[1],
    access_token: match[2],
  };

  return tokens;
};

const get_data = async () => {
  const username = process.env.KUBIOS_USERNAME;
  const password = process.env.KUBIOS_PASSWORD;
  const client_id = process.env.KUBIOS_CLIENT_ID;

  tokens = await user_login(username, password, client_id);

  const headers = new Headers();
  headers.append("User-Agent", USER_AGENT);
  headers.append("Authorization", tokens.id_token);

  let response = await fetch("https://analysis.kubioscloud.com/v1/user/self", {
    method: "GET",
    headers: headers,
  });
  const user_info = await response.json();

  response = await fetch(
    "https://analysis.kubioscloud.com/v2/result/self" +
      "?from=2023-01-01T00%3A00%3A00%2B00%3A00",
    {
      method: "GET",
      headers: headers,
    }
  );
  const all_results = await response.json();
  const data = {
    results: all_results.results,
    user_info: user_info.user,
  };
  return data;
};

//get_data().then((x) => console.log(x));
module.exports = { get_data, user_login };