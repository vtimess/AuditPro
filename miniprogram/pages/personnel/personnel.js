const { personnelApi } = require("../../api/index");

Page({
  data: {
    loading: false,
    records: [],
    keyword: ""
  },

  onShow() { this.loadRecords(); },
  onPullDownRefresh() { this.loadRecords().finally(() => wx.stopPullDownRefresh()); },
  inputKeyword(e) { this.setData({ keyword: e.detail.value }); },
  openEntry() { wx.navigateTo({ url: "/pages/personnel-entry/personnel-entry" }); },
  editRecord(e) { wx.navigateTo({ url: `/pages/personnel-entry/personnel-entry?id=${e.currentTarget.dataset.id}` }); },

  async loadRecords() {
    this.setData({ loading: true });
    try {
      const records = await personnelApi.list(this.data.keyword);
      this.setData({ records });
    } catch (error) { wx.showToast({ title: error.message, icon: "none" }); }
    finally { this.setData({ loading: false }); }
  },

  async exportRoster() {
    wx.showLoading({ title: "正在导出" });
    try {
      const filePath = await personnelApi.exportRoster();
      wx.openDocument({ filePath, fileType: "xlsx", showMenu: true });
    } catch (error) {
      wx.showToast({ title: error.message || "文件下载失败", icon: "none" });
    } finally {
      wx.hideLoading();
    }
  },

  deleteRecord(e) {
    const id = e.currentTarget.dataset.id;
    wx.showModal({
      title: "删除人员",
      content: "删除后将不再出现在人员花名册，是否继续？",
      success: async result => {
        if (!result.confirm) return;
        try {
          await personnelApi.remove(id);
          await this.loadRecords();
          wx.showToast({ title: "已删除", icon: "success" });
        } catch (error) { wx.showToast({ title: error.message, icon: "none" }); }
      }
    });
  }
});
