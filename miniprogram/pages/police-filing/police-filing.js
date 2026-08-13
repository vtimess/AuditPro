const { request } = require("../../utils/request");
const { API_BASE_URL } = require("../../config/index");

const emptyForm = () => ({
  person_name: "", gender: "男", id_card: "", company_name: "", region: "镇江",
  mobile: "", filing_status: "pending", filing_date: "", remarks: ""
});

Page({
  data: {
    activeTab: "list", loading: false, records: [], keyword: "", form: emptyForm(), editingId: null,
    genderOptions: ["男", "女"], genderIndex: 0,
    statusOptions: [
      { value: "pending", label: "待备案" }, { value: "filed", label: "已备案" },
      { value: "not_required", label: "无需备案" }
    ], statusIndex: 0
  },

  onLoad() { this.loadRecords(); },
  onPullDownRefresh() { this.loadRecords().finally(() => wx.stopPullDownRefresh()); },
  switchTab(e) { this.setData({ activeTab: e.currentTarget.dataset.tab }); },
  inputKeyword(e) { this.setData({ keyword: e.detail.value }); },
  inputField(e) { this.setData({ [`form.${e.currentTarget.dataset.field}`]: e.detail.value }); },
  changeGender(e) {
    const index = Number(e.detail.value);
    this.setData({ genderIndex: index, "form.gender": this.data.genderOptions[index] });
  },
  changeStatus(e) {
    const index = Number(e.detail.value);
    this.setData({ statusIndex: index, "form.filing_status": this.data.statusOptions[index].value });
  },
  changeDate(e) { this.setData({ "form.filing_date": e.detail.value }); },

  async loadRecords() {
    this.setData({ loading: true });
    try {
      const keyword = encodeURIComponent(this.data.keyword.trim());
      const records = await request({ url: `/police-filings?keyword=${keyword}` });
      const names = { pending: "待备案", filed: "已备案", not_required: "无需备案" };
      this.setData({ records: records.map(item => ({ ...item, status_text: names[item.filing_status] })) });
    } catch (error) { wx.showToast({ title: error.message, icon: "none" }); }
    finally { this.setData({ loading: false }); }
  },

  async submit() {
    const form = { ...this.data.form };
    if (!form.person_name || !form.id_card || !form.company_name || !form.region) {
      wx.showToast({ title: "请填写姓名、身份证号、公司和地区", icon: "none" }); return;
    }
    if (form.filing_status !== "filed") delete form.filing_date;
    try {
      await request({ url: this.data.editingId ? `/police-filings/${this.data.editingId}` : "/police-filings", method: this.data.editingId ? "PUT" : "POST", data: form });
      wx.showToast({ title: "保存成功", icon: "success" });
      this.setData({ form: emptyForm(), genderIndex: 0, statusIndex: 0, editingId: null, activeTab: "list" });
      await this.loadRecords();
    } catch (error) { wx.showToast({ title: error.message, icon: "none" }); }
  },

  exportExcel() {
    const token = wx.getStorageSync("access_token");
    wx.showLoading({ title: "正在导出" });
    wx.downloadFile({
      url: `${API_BASE_URL}/police-filings/export`, header: { Authorization: `Bearer ${token}` },
      success: (result) => {
        if (result.statusCode !== 200) { wx.showToast({ title: "导出失败", icon: "none" }); return; }
        wx.openDocument({ filePath: result.tempFilePath, fileType: "xlsx", showMenu: true });
      },
      fail: () => wx.showToast({ title: "导出失败", icon: "none" }), complete: () => wx.hideLoading()
    });
  },
  async editRecord(e) {
    try {
      const record = await request({ url: `/police-filings/${e.currentTarget.dataset.id}` });
      const genderIndex = this.data.genderOptions.indexOf(record.gender);
      const statusIndex = this.data.statusOptions.findIndex(item => item.value === record.filing_status);
      const { id, created_at, ...form } = record;
      this.setData({ form: { ...emptyForm(), ...form, filing_date: form.filing_date || "" }, editingId: id, genderIndex, statusIndex, activeTab: "form" });
    } catch (error) { wx.showToast({ title: error.message, icon: "none" }); }
  },
  deleteRecord(e) {
    const id = e.currentTarget.dataset.id;
    wx.showModal({ title: "删除备案信息", content: "删除后将不再显示，是否继续？", success: async result => {
      if (!result.confirm) return;
      try { await request({ url: `/police-filings/${id}`, method: "DELETE" }); await this.loadRecords(); wx.showToast({ title: "已删除", icon: "success" }); }
      catch (error) { wx.showToast({ title: error.message, icon: "none" }); }
    }});
  }
});
