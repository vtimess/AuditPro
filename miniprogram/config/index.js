// 发布生产版本时使用 production，本地联调时改为 test。
const API_ENV = "production";

const API_ENVIRONMENTS = {
  test: "http://127.0.0.1:8000/api/v1",
  production: "https://www.vtimess.cn/api/v1"
};

if (!API_ENVIRONMENTS[API_ENV]) {
  throw new Error(`未知的小程序接口环境：${API_ENV}`);
}

module.exports = {
  API_ENV,
  API_BASE_URL: API_ENVIRONMENTS[API_ENV]
};
