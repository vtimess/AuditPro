const { authApi } = require("../../api/index");

function getWechatProfile() {
  return new Promise((resolve, reject) => {
    wx.getUserProfile({
      desc: "用于完善港务审计平台用户资料",
      success: resolve,
      fail: reject
    });
  });
}

function getLoginCode() {
  return new Promise((resolve, reject) => {
    wx.login({ success: resolve, fail: reject });
  });
}

Page({
  data: {
    loading: false,
    privacyChecked: false
  },

  onLoad() {
    if (wx.getStorageSync("access_token")) {
      wx.switchTab({ url: "/pages/home/home" });
    }
  },

  togglePrivacy() {
    this.setData({ privacyChecked: !this.data.privacyChecked });
  },

  async login() {
    if (!this.data.privacyChecked) {
      wx.showToast({ title: "请先同意隐私说明", icon: "none" });
      return;
    }
    if (this.data.loading) return;
    this.setData({ loading: true });
    try {
      try {
        const result = await getWechatProfile();
        const profile = result.userInfo;
        if (!profile || !profile.avatarUrl) {
          throw new Error("未获取到微信头像，请重新授权");
        }
        const loginResult = await getLoginCode();
        if (!loginResult.code) throw new Error("未获取到微信登录凭证");
        const loginData = await authApi.wechatLogin({
          code: loginResult.code,
          nickname: profile.nickName || "微信用户",
          avatar_url: profile.avatarUrl
        });
        getApp().setSession(loginData.access_token, loginData.user);
        wx.switchTab({ url: "/pages/home/home" });
      } catch (error) {
        const denied = error.errMsg && error.errMsg.includes("getUserProfile:fail auth deny");
        throw new Error(denied ? "需要授权微信头像后才能登录" : (error.message || "微信授权失败"));
      }
    } catch (error) {
      wx.showToast({ title: error.message || "登录失败", icon: "none", duration: 2500 });
    } finally {
      this.setData({ loading: false });
    }
  }
});
