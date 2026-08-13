const { request } = require("../../utils/request");
const { uploadImage } = require("../../utils/upload");

function nowText() { const d = new Date(); const p = n => String(n).padStart(2, "0"); return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:00`; }
const emptyForm = () => ({ inspection_project: "", region: "镇江", inspection_area: "", inspected_at: nowText(), inspectors: "", location_text: "", weather: "", site_readiness: "normal", environment_status: "normal", equipment_status: "normal", fire_status: "normal", ppe_status: "normal", work_order_status: "normal", description: "", hazards: [] });
const emptyHazard = () => ({ hazard_name: "", category: "人员行为", risk_level: "general", description: "", responsible_person: "", rectification_deadline: "", rectification_requirement: "", immediate_stop: false, images: [] });

Page({
  data: {
    activeTab: "check", form: emptyForm(), inspections: [], rectifications: [], loading: false,
    inspectionImages: [], checkImages: {}, checkPhotoCounts: {}, hazardVisible: false,
    hazard: emptyHazard(), editingHazardIndex: -1, hazardRiskIndex: 0, canReview: false,
    checkItems: [{key:"environment_status",name:"环境卫生"},{key:"equipment_status",name:"设备设施"},{key:"fire_status",name:"消防设施"},{key:"ppe_status",name:"劳保用品"},{key:"work_order_status",name:"作业秩序"}],
    statusOptions: [{ value: "normal", label: "正常" }, { value: "abnormal", label: "异常" }, { value: "not_applicable", label: "不适用" }],
    readinessOptions: [{ value: "normal", label: "正常" }, { value: "basic", label: "基本正常" }, { value: "rectification", label: "需整改" }],
    categories: ["人员行为", "设备设施", "作业环境", "消防", "用电", "交通", "其他"],
    riskOptions: [{ value: "general", label: "一般" }, { value: "high", label: "较大" }, { value: "major", label: "重大" }]
  },
  onLoad() {
    const user = wx.getStorageSync("current_user") || {};
    this.setData({ "form.inspectors": user.real_name || "", canReview: ["regional_safety_manager", "project_leader"].includes(user.role_code) });
    this.loadData();
  },
  onPullDownRefresh() { this.loadData().finally(() => wx.stopPullDownRefresh()); },
  switchTab(e) { this.setData({ activeTab: e.currentTarget.dataset.tab }); },
  inputField(e) { this.setData({ [`form.${e.currentTarget.dataset.field}`]: e.detail.value }); },
  inputHazard(e) { this.setData({ [`hazard.${e.currentTarget.dataset.field}`]: e.detail.value }); },
  selectCheckStatus(e) {
    const field = e.currentTarget.dataset.field;
    const value = e.currentTarget.dataset.value;
    const changes = { [`form.${field}`]: value };
    if (value !== "abnormal") {
      changes[`checkImages.${field}`] = [];
      changes[`checkPhotoCounts.${field}`] = 0;
    }
    this.setData(changes);
  },
  selectReadiness(e) { this.setData({ "form.site_readiness": e.currentTarget.dataset.value }); },
  chooseLocation() {
    wx.chooseLocation({
      success: result => {
        const locationName = (result.name || result.address || "").trim();
        if (!locationName) { wx.showToast({ title: "未获取到位置名称", icon: "none" }); return; }
        this.setData({ "form.location_text": locationName });
      },
      fail: error => {
        if (!String(error.errMsg || "").includes("cancel")) wx.showToast({ title: "位置获取失败，请检查定位权限", icon: "none" });
      }
    });
  },
  chooseCheckImage(e) {
    const field = e.currentTarget.dataset.field;
    const current = this.data.checkImages[field] || [];
    if (current.length >= 9) { wx.showToast({ title: "每项最多拍摄9张照片", icon: "none" }); return; }
    wx.chooseMedia({
      count: 9 - current.length,
      mediaType: ["image"],
      sourceType: ["camera"],
      success: result => {
        const images = current.concat(result.tempFiles.map(item => item.tempFilePath));
        this.setData({ [`checkImages.${field}`]: images, [`checkPhotoCounts.${field}`]: images.length });
      }
    });
  },
  previewCheckImages(e) {
    const images = this.data.checkImages[e.currentTarget.dataset.field] || [];
    if (images.length) wx.previewImage({ current: images[0], urls: images });
  },
  async loadData() {
    this.setData({ loading: true });
    try {
      const [inspections, rectifications] = await Promise.all([request({ url: "/safety-inspections" }), request({ url: "/safety-inspections/rectifications" })]);
      const riskNames = { general: "一般", high: "较大", major: "重大" }, statusNames = { pending: "待整改", pending_review: "待复查", completed: "已完成" };
      this.setData({ inspections: inspections.map(i => ({ ...i, risk_text: riskNames[i.highest_risk_level] || "无危险点" })), rectifications: rectifications.map(i => ({ ...i, risk_text: riskNames[i.risk_level], status_text: statusNames[i.status] })) });
    } catch (error) { wx.showToast({ title: error.message, icon: "none" }); }
    finally { this.setData({ loading: false }); }
  },
  chooseInspectionImage() { wx.chooseMedia({ count: 9 - this.data.inspectionImages.length, mediaType: ["image"], sourceType: ["camera", "album"], success: r => this.setData({ inspectionImages: this.data.inspectionImages.concat(r.tempFiles.map(i => i.tempFilePath)) }) }); },
  openHazard() { this.setData({ hazardVisible: true, hazard: emptyHazard(), editingHazardIndex: -1 }); },
  closeHazard() { this.setData({ hazardVisible: false }); },
  changeHazardCategory(e) { const i = Number(e.detail.value); this.setData({ "hazard.category": this.data.categories[i] }); },
  changeHazardRisk(e) { const i = Number(e.detail.value); this.setData({ "hazard.risk_level": this.data.riskOptions[i].value, hazardRiskIndex: i }); },
  changeDeadline(e) { this.setData({ "hazard.rectification_deadline": e.detail.value }); },
  toggleStop(e) { this.setData({ "hazard.immediate_stop": e.detail.value }); },
  chooseHazardImage() { wx.chooseMedia({ count: 9 - this.data.hazard.images.length, mediaType: ["image"], sourceType: ["camera", "album"], success: r => this.setData({ "hazard.images": this.data.hazard.images.concat(r.tempFiles.map(i => i.tempFilePath)) }) }); },
  saveHazard() {
    const h = this.data.hazard;
    if (!h.hazard_name || !h.description || !h.responsible_person || !h.rectification_deadline || !h.rectification_requirement) { wx.showToast({ title: "请填写完整危险点信息", icon: "none" }); return; }
    const hazards = [...this.data.form.hazards, h]; this.setData({ "form.hazards": hazards, hazardVisible: false });
  },
  removeHazard(e) { const hazards = [...this.data.form.hazards]; hazards.splice(Number(e.currentTarget.dataset.index), 1); this.setData({ "form.hazards": hazards }); },
  async submitInspection() {
    const form = { ...this.data.form };
    if (!form.inspection_project || !form.inspection_area || !form.inspectors) { wx.showToast({ title: "请填写项目、区域和检查人员", icon: "none" }); return; }
    const missingPhotoItem = this.data.checkItems.find(item => form[item.key] === "abnormal" && !(this.data.checkImages[item.key] || []).length);
    if (missingPhotoItem) { wx.showToast({ title: `${missingPhotoItem.name}异常时请现场拍照`, icon: "none" }); return; }
    const imageGroups = form.hazards.map(h => h.images || []); form.hazards = form.hazards.map(({ images, ...rest }) => rest);
    try {
      wx.showLoading({ title: "正在保存", mask: true });
      const record = await request({ url: "/safety-inspections", method: "POST", data: form });
      for (const path of this.data.inspectionImages) await uploadImage(path, "safety_inspection", record.id, "site");
      for (const item of this.data.checkItems) {
        for (const path of this.data.checkImages[item.key] || []) await uploadImage(path, "safety_inspection", record.id, `check_${item.key}`);
      }
      for (let i = 0; i < record.hazards.length; i++) for (const path of imageGroups[i] || []) await uploadImage(path, "safety_hazard", record.hazards[i].id, "hazard");
      const user = wx.getStorageSync("current_user") || {}; const next = emptyForm(); next.inspectors = user.real_name || "";
      this.setData({ form: next, inspectionImages: [], checkImages: {}, checkPhotoCounts: {}, activeTab: "records" }); await this.loadData(); wx.showToast({ title: "保存成功", icon: "success" });
    } catch (error) { wx.showToast({ title: error.message, icon: "none" }); }
    finally { wx.hideLoading(); }
  },
  rectify(e) {
    const id = e.currentTarget.dataset.id;
    wx.chooseMedia({ count: 9, mediaType: ["image"], sourceType: ["camera", "album"], success: media => {
      wx.showModal({ title: "提交整改", editable: true, placeholderText: "请输入整改说明", success: async r => {
        if (!r.confirm || !r.content.trim()) return;
        try {
          wx.showLoading({ title: "正在提交", mask: true });
          await request({ url: `/safety-inspections/hazards/${id}/rectify`, method: "POST", data: { description: r.content.trim() } });
          for (const item of media.tempFiles) await uploadImage(item.tempFilePath, "safety_hazard", id, "rectification");
          await this.loadData(); wx.showToast({ title: "已提交复查", icon: "success" });
        } catch (error) { wx.showToast({ title: error.message, icon: "none" }); }
        finally { wx.hideLoading(); }
      }});
    }});
  },
  review(e) {
    const id = e.currentTarget.dataset.id;
    wx.showActionSheet({ itemList: ["复查通过", "复查不通过"], success: action => {
      const result = action.tapIndex === 0 ? "approved" : "rejected";
      wx.showModal({ title: result === "approved" ? "复查通过" : "复查不通过", editable: true, placeholderText: "请输入复查意见", success: async modal => {
        if (!modal.confirm || !modal.content.trim()) return;
        try {
          await request({ url: `/safety-inspections/hazards/${id}/review`, method: "POST", data: { result, comment: modal.content.trim() } });
          await this.loadData(); wx.showToast({ title: "复查完成", icon: "success" });
        } catch (error) { wx.showToast({ title: error.message, icon: "none" }); }
      }});
    }});
  }
});
