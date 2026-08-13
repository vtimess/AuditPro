const { API_BASE_URL } = require("../config/index");

function uploadImage(filePath, businessType, businessId, usageType) {
  const token = wx.getStorageSync("access_token");
  return new Promise((resolve, reject) => {
    wx.uploadFile({
      url: `${API_BASE_URL}/files/upload`, filePath, name: "file",
      formData: { business_type: businessType, business_id: String(businessId), usage_type: usageType || "general" },
      header: { Authorization: `Bearer ${token}` },
      success(response) {
        let body;
        try { body = JSON.parse(response.data); } catch (_) { reject(new Error("上传响应格式错误")); return; }
        if (response.statusCode < 200 || response.statusCode >= 300) { reject(new Error(body.detail || body.message || "图片上传失败")); return; }
        resolve(body.data);
      },
      fail(error) { reject(new Error(error.errMsg || "图片上传失败")); }
    });
  });
}

module.exports = { uploadImage };
