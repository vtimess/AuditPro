const { request } = require("../../utils/request");
const { uploadImage } = require("../../utils/upload");
const { API_BASE_URL } = require("../../config/index");

function today() { const d = new Date(); const p = n => String(n).padStart(2, "0"); return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`; }
const emptyForm = () => ({ category: "办公用品", item_name: "", quantity: "1", unit: "件", unit_price: "", total_amount: "", total_adjustment_reason: "", purchase_date: today(), supplier_name: "", invoice_number: "", region: "镇江", description: "" });

Page({
  data: {
    activeTab: "list", loading: false, records: [], keyword: "", selectedIds: [], allSelected: false,
    form: emptyForm(), invoiceImages: [], editingId: null,
    categories: ["办公用品", "劳保用品", "清洁用品", "设备配件", "其他"], categoryIndex: 0,
    units: ["件", "个", "箱", "套", "公斤", "批"], unitIndex: 0, calculatedTotal: "0.00", manualTotal: false
  },
  onLoad() { this.loadRecords(); },
  onPullDownRefresh() { this.loadRecords().finally(() => wx.stopPullDownRefresh()); },
  switchTab(e) { this.setData({ activeTab: e.currentTarget.dataset.tab }); },
  inputKeyword(e) { this.setData({ keyword: e.detail.value }); },
  inputField(e) { this.setData({ [`form.${e.currentTarget.dataset.field}`]: e.detail.value }); },
  inputAmount(e) { this.setData({ [`form.${e.currentTarget.dataset.field}`]: e.detail.value }, () => this.recalculate()); },
  inputTotal(e) {
    const value = e.detail.value;
    this.setData({ "form.total_amount": value, manualTotal: value !== "" && Number(value).toFixed(2) !== this.data.calculatedTotal });
  },
  recalculate() {
    const total = (Number(this.data.form.quantity || 0) * Number(this.data.form.unit_price || 0)).toFixed(2);
    this.setData({ calculatedTotal: total, "form.total_amount": total, manualTotal: false, "form.total_adjustment_reason": "" });
  },
  changeCategory(e) { const i = Number(e.detail.value); this.setData({ categoryIndex: i, "form.category": this.data.categories[i] }); },
  changeUnit(e) { const i = Number(e.detail.value); this.setData({ unitIndex: i, "form.unit": this.data.units[i] }); },
  changeDate(e) { this.setData({ "form.purchase_date": e.detail.value }); },
  async loadRecords() {
    this.setData({ loading: true });
    try {
      const records = await request({ url: `/consumable-purchases?keyword=${encodeURIComponent(this.data.keyword.trim())}` });
      this.setData({ records: records.map(item => ({ ...item, selected: false })), selectedIds: [], allSelected: false });
    }
    catch (error) { wx.showToast({ title: error.message, icon: "none" }); }
    finally { this.setData({ loading: false }); }
  },
  toggleRecord(e) {
    const id = Number(e.currentTarget.dataset.id);
    const records = this.data.records.map(item => item.id === id ? { ...item, selected: !item.selected } : item);
    const selectedIds = records.filter(item => item.selected).map(item => item.id);
    this.setData({ records, selectedIds, allSelected: records.length > 0 && selectedIds.length === records.length });
  },
  toggleSelectAll() {
    const selected = !this.data.allSelected;
    const records = this.data.records.map(item => ({ ...item, selected }));
    this.setData({ records, allSelected: selected, selectedIds: selected ? records.map(item => item.id) : [] });
  },
  exportSelected() {
    if (!this.data.selectedIds.length) { wx.showToast({ title: "请先选择需要导出的记录", icon: "none" }); return; }
    this.downloadExcel(this.data.selectedIds);
  },
  exportAll() { this.downloadExcel([]); },
  downloadExcel(ids) {
    const token = wx.getStorageSync("access_token");
    wx.showLoading({ title: "正在导出" });
    wx.downloadFile({
      url: `${API_BASE_URL}/consumable-purchases/export${ids.length ? `?ids=${ids.join(",")}` : ""}`,
      header: { Authorization: `Bearer ${token}` },
      success: result => {
        if (result.statusCode !== 200) { wx.showToast({ title: "导出失败", icon: "none" }); return; }
        wx.openDocument({ filePath: result.tempFilePath, fileType: "xlsx", showMenu: true });
      }, fail: () => wx.showToast({ title: "导出失败", icon: "none" }), complete: () => wx.hideLoading()
    });
  },
  chooseInvoice() {
    wx.chooseMedia({ count: 9 - this.data.invoiceImages.length, mediaType: ["image"], sourceType: ["album", "camera"], success: result => this.setData({ invoiceImages: this.data.invoiceImages.concat(result.tempFiles.map(item => item.tempFilePath)) }) });
  },
  removeImage(e) { const images = [...this.data.invoiceImages]; images.splice(Number(e.currentTarget.dataset.index), 1); this.setData({ invoiceImages: images }); },
  previewImage(e) { wx.previewImage({ current: e.currentTarget.dataset.src, urls: this.data.invoiceImages }); },
  async submit() {
    const form = { ...this.data.form };
    if (!form.item_name || !form.quantity || form.unit_price === "" || form.total_amount === "" || !form.region) { wx.showToast({ title: "请填写完整采购信息", icon: "none" }); return; }
    if (this.data.manualTotal && !form.total_adjustment_reason.trim()) { wx.showToast({ title: "请填写总价调整原因", icon: "none" }); return; }
    try {
      wx.showLoading({ title: "正在保存", mask: true });
      const record = await request({ url: this.data.editingId ? `/consumable-purchases/${this.data.editingId}` : "/consumable-purchases", method: this.data.editingId ? "PUT" : "POST", data: form });
      for (const path of this.data.invoiceImages) await uploadImage(path, "consumable_purchase", record.id, "invoice");
      this.setData({ form: emptyForm(), invoiceImages: [], editingId: null, calculatedTotal: "0.00", manualTotal: false, activeTab: "list" });
      await this.loadRecords(); wx.showToast({ title: "保存成功", icon: "success" });
    } catch (error) { wx.showToast({ title: error.message, icon: "none" }); }
    finally { wx.hideLoading(); }
  }
  ,async editRecord(e) {
    try {
      const record = await request({ url: `/consumable-purchases/${e.currentTarget.dataset.id}` });
      const categoryIndex = Math.max(0, this.data.categories.indexOf(record.category));
      const unitIndex = Math.max(0, this.data.units.indexOf(record.unit));
      this.setData({
        form: { ...emptyForm(), ...record, quantity: String(record.quantity), unit_price: String(record.unit_price), total_amount: String(record.total_amount) },
        editingId: record.id, invoiceImages: [], categoryIndex, unitIndex,
        calculatedTotal: Number(record.calculated_total).toFixed(2), manualTotal: record.is_manual_total, activeTab: "form"
      });
    } catch (error) { wx.showToast({ title: error.message, icon: "none" }); }
  }
  ,deleteRecord(e) {
    const id = e.currentTarget.dataset.id;
    wx.showModal({ title: "删除采购记录", content: "删除后将不再显示，是否继续？", success: async result => {
      if (!result.confirm) return;
      try { await request({ url: `/consumable-purchases/${id}`, method: "DELETE" }); await this.loadRecords(); wx.showToast({ title: "已删除", icon: "success" }); }
      catch (error) { wx.showToast({ title: error.message, icon: "none" }); }
    }});
  }
});
