const { API_BASE_URL } = require("../config/index");

function request(options) {
  const app = getApp();
  const token = wx.getStorageSync("access_token") || app.globalData.token;
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${API_BASE_URL}${options.url}`,
      method: options.method || "GET",
      data: options.data || {},
      timeout: 12000,
      header: {
        "content-type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(options.header || {})
      },
      success(response) {
        if (response.statusCode === 401) {
          app.clearSession();
          wx.reLaunch({ url: "/pages/login/login" });
          reject(new Error("登录已过期"));
          return;
        }
        if (response.statusCode < 200 || response.statusCode >= 300) {
          const message = response.data && (response.data.detail || response.data.message);
          reject(new Error(message || "服务请求失败"));
          return;
        }
        resolve(response.data.data);
      },
      fail(error) {
        reject(new Error(error.errMsg || "网络连接失败"));
      }
    });
  });
}

module.exports = { request };
