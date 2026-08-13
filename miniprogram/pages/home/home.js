const { request } = require("../../utils/request");

Page({
  data: {
    loading: true,
    home: null
  },

  onShow() {
    if (!wx.getStorageSync("access_token")) {
      wx.reLaunch({ url: "/pages/login/login" });
      return;
    }
    this.loadHome();
  },

  onPullDownRefresh() {
    this.loadHome().finally(() => wx.stopPullDownRefresh());
  },

  async loadHome() {
    this.setData({ loading: !this.data.home });
    try {
      const home = await request({ url: "/home" });
      this.setData({ home });
    } catch (error) {
      wx.showToast({ title: error.message || "加载失败", icon: "none" });
    } finally {
      this.setData({ loading: false });
    }
  },

  openWorkbench() {
    wx.switchTab({ url: "/pages/workbench/workbench" });
  }
});
