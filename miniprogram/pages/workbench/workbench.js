const { homeApi } = require("../../api/index");

Page({
  data: {
    loading: true,
    groups: []
  },

  onShow() {
    if (!wx.getStorageSync("access_token")) {
      wx.reLaunch({ url: "/pages/login/login" });
      return;
    }
    this.loadModules();
  },

  onPullDownRefresh() {
    this.loadModules().finally(() => wx.stopPullDownRefresh());
  },

  async loadModules() {
    try {
      const result = await homeApi.getWorkbench();
      const grouped = {};
      result.modules.forEach((item) => {
        if (!grouped[item.group]) grouped[item.group] = [];
        grouped[item.group].push(item);
      });
      const groups = Object.keys(grouped).map((name) => ({ name, modules: grouped[name] }));
      this.setData({ groups });
    } catch (error) {
      wx.showToast({ title: error.message || "加载失败", icon: "none" });
    } finally {
      this.setData({ loading: false });
    }
  },

  openModule(event) {
    const { enabled, name, key } = event.currentTarget.dataset;
    const routes = {
      attendance: "/pages/attendance/attendance",
      personnel_management: "/pages/personnel/personnel",
      police_filing: "/pages/police-filing/police-filing",
      consumable_purchase: "/pages/consumable/consumable",
      safety_inspection: "/pages/safety/safety",
      emergency_drill: "/pages/emergency-drill/emergency-drill"
    };
    if (enabled && routes[key]) {
      wx.navigateTo({ url: routes[key] });
      return;
    }
    if (!enabled) {
      wx.showToast({ title: `${name}暂未开放`, icon: "none" });
    }
  }
});
