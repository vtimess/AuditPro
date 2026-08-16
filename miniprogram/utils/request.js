const { API_BASE_URL } = require("../config/index");

function getErrorMessage(data) {
  const detail = data && (data.detail || data.message);
  if (Array.isArray(detail) && detail.length) {
    const first = detail[0] || {};
    return String(first.msg || "提交数据校验失败").replace(/^Value error,\s*/, "");
  }
  return typeof detail === "string" ? detail : "服务请求失败";
}

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
          reject(new Error(getErrorMessage(response.data)));
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

function resolveApiUrl(path) {
  if (/^https?:\/\//.test(path)) return path;
  if (path.startsWith("/api/v1/")) {
    return `${API_BASE_URL.replace(/\/api\/v1\/?$/, "")}${path}`;
  }
  return `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

function uploadFile(options) {
  const app = getApp();
  const token = wx.getStorageSync("access_token") || app.globalData.token;
  return new Promise((resolve, reject) => {
    wx.uploadFile({
      url: resolveApiUrl(options.url),
      filePath: options.filePath,
      name: options.name || "file",
      formData: options.formData || {},
      timeout: options.timeout || 60000,
      header: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(options.header || {})
      },
      success(response) {
        let body;
        try {
          body = JSON.parse(response.data);
        } catch (_) {
          reject(new Error("上传响应格式错误"));
          return;
        }
        if (response.statusCode === 401) {
          app.clearSession();
          wx.reLaunch({ url: "/pages/login/login" });
          reject(new Error("登录已过期"));
          return;
        }
        if (response.statusCode < 200 || response.statusCode >= 300) {
          reject(new Error(getErrorMessage(body)));
          return;
        }
        resolve(body.data);
      },
      fail(error) {
        reject(new Error(error.errMsg || "文件上传失败"));
      }
    });
  });
}

function downloadFile(path) {
  const app = getApp();
  const token = wx.getStorageSync("access_token") || app.globalData.token;
  return new Promise((resolve, reject) => {
    wx.downloadFile({
      url: resolveApiUrl(path),
      timeout: 60000,
      header: token ? { Authorization: `Bearer ${token}` } : {},
      success(response) {
        if (response.statusCode === 401) {
          app.clearSession();
          wx.reLaunch({ url: "/pages/login/login" });
          reject(new Error("登录已过期"));
          return;
        }
        if (response.statusCode < 200 || response.statusCode >= 300) {
          reject(new Error("文件下载失败"));
          return;
        }
        resolve(response.tempFilePath);
      },
      fail(error) {
        reject(new Error(error.errMsg || "文件下载失败"));
      }
    });
  });
}

module.exports = { request, uploadFile, downloadFile };
