App({
  globalData: {
    token: "",
    user: null
  },

  onLaunch() {
    this.globalData.token = wx.getStorageSync("access_token") || "";
    this.globalData.user = wx.getStorageSync("current_user") || null;
  },

  setSession(token, user) {
    this.globalData.token = token;
    this.globalData.user = user;
    wx.setStorageSync("access_token", token);
    wx.setStorageSync("current_user", user);
  },

  clearSession() {
    this.globalData.token = "";
    this.globalData.user = null;
    wx.removeStorageSync("access_token");
    wx.removeStorageSync("current_user");
  }
});
