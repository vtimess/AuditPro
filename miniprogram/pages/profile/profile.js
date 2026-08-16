const { profileApi } = require("../../api/index");

Page({
  data: {
    loading: true,
    user: null,
    avatarText: "用"
  },

  onShow() {
    if (!wx.getStorageSync("access_token")) {
      wx.reLaunch({ url: "/pages/login/login" });
      return;
    }
    this.loadProfile();
  },

  async loadProfile() {
    try {
      const user = await profileApi.get();
      getApp().globalData.user = user;
      wx.setStorageSync("current_user", user);
      this.setData({ user, avatarText: (user.real_name || "用").slice(0, 1) });
    } catch (error) {
      wx.showToast({ title: error.message || "加载失败", icon: "none" });
    } finally {
      this.setData({ loading: false });
    }
  },

  editName() {
    const current = this.data.user ? this.data.user.real_name : "";
    wx.showModal({
      title: "修改姓名",
      editable: true,
      placeholderText: "请输入真实姓名",
      content: current,
      success: async (result) => {
        const name = (result.content || "").trim();
        if (!result.confirm || !name || name === current) return;
        try {
          const user = await profileApi.update({ real_name: name });
          this.setData({ user, avatarText: (user.real_name || "用").slice(0, 1) });
          wx.setStorageSync("current_user", user);
          wx.showToast({ title: "已保存", icon: "success" });
        } catch (error) {
          wx.showToast({ title: error.message || "保存失败", icon: "none" });
        }
      }
    });
  },

  showComingSoon(event) {
    wx.showToast({ title: `${event.currentTarget.dataset.name}暂未开放`, icon: "none" });
  },

  logout() {
    wx.showModal({
      title: "退出登录",
      content: "确定退出当前账号吗？",
      success: (result) => {
        if (!result.confirm) return;
        getApp().clearSession();
        wx.reLaunch({ url: "/pages/login/login" });
      }
    });
  }
});
