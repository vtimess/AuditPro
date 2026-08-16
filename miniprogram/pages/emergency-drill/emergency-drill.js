const { emergencyDrillApi } = require("../../api/index");

function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function fileType(fileName) {
  return String(fileName).split(".").pop().toLowerCase();
}

function safeExportName(fileName) {
  const name = String(fileName || "应急演练方案").replace(/[\\/:*?"<>|]/g, "_").trim();
  return name || "应急演练方案";
}

Page({
  data: {
    loading: false,
    importing: false,
    records: [],
    keyword: ""
  },

  onShow() { this.loadRecords(); },
  onPullDownRefresh() { this.loadRecords().finally(() => wx.stopPullDownRefresh()); },
  inputKeyword(e) { this.setData({ keyword: e.detail.value }); },

  async loadRecords() {
    this.setData({ loading: true });
    try {
      const records = await emergencyDrillApi.list(this.data.keyword);
      this.setData({
        records: records.map(item => ({
          ...item,
          size_text: formatFileSize(item.file_size),
          created_text: item.created_at.replace("T", " ")
        }))
      });
    } catch (error) {
      wx.showToast({ title: error.message || "加载失败", icon: "none" });
    } finally {
      this.setData({ loading: false });
    }
  },

  chooseDocument() {
    if (this.data.importing) return;
    wx.chooseMessageFile({
      count: 1,
      type: "file",
      extension: ["doc", "docx", "pdf"],
      success: result => this.uploadDocument(result.tempFiles[0])
    });
  },

  async uploadDocument(file) {
    this.setData({ importing: true });
    wx.showLoading({ title: "正在导入", mask: true });
    try {
      await emergencyDrillApi.importDocument(file);
      wx.showToast({ title: "方案导入成功", icon: "success" });
      await this.loadRecords();
    } catch (error) {
      wx.showToast({ title: error.message || "导入失败", icon: "none" });
    } finally {
      wx.hideLoading();
      this.setData({ importing: false });
    }
  },

  previewDocument(e) {
    const { url, name } = e.currentTarget.dataset;
    this.downloadDocument(url, name, false);
  },

  exportDocument(e) {
    const { url, name } = e.currentTarget.dataset;
    this.downloadDocument(url, name, true);
  },

  async downloadDocument(path, fileName, showMenu) {
    wx.showLoading({ title: showMenu ? "正在导出" : "正在加载", mask: true });
    try {
      const filePath = await emergencyDrillApi.download(path);
      if (showMenu) {
        this.saveAndOpenExport(filePath, fileName);
      } else {
        this.openDocument(filePath, fileName, false);
      }
    } catch (error) {
      wx.showToast({ title: error.message || (showMenu ? "方案导出失败" : "方案预览失败"), icon: "none" });
    } finally {
      wx.hideLoading();
    }
  },

  saveAndOpenExport(tempFilePath, fileName) {
    const fileSystem = wx.getFileSystemManager();
    const targetPath = `${wx.env.USER_DATA_PATH}/${safeExportName(fileName)}`;
    const saveFile = () => {
      fileSystem.saveFile({
        tempFilePath,
        filePath: targetPath,
        success: result => this.openDocument(result.savedFilePath || targetPath, fileName, true),
        fail: () => wx.showToast({ title: "方案文件保存失败", icon: "none" })
      });
    };
    fileSystem.unlink({ filePath: targetPath, complete: saveFile });
  },

  openDocument(filePath, fileName, showMenu) {
    wx.openDocument({
      filePath,
      fileType: fileType(fileName),
      showMenu,
      fail: () => wx.showToast({ title: "文件打开失败", icon: "none" })
    });
  }
});
