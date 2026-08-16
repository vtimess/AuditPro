const { policeFilingApi } = require("../../api/index");

const genderOptions = ["男", "女"];
const regionOptions = ["镇江", "南京"];
const statusOptions = [
  { value: "pending", label: "待备案" },
  { value: "filed", label: "已备案" },
  { value: "not_required", label: "无需备案" }
];
const emptyForm = () => ({
  person_name: "", gender: "男", id_card: "", age: "", company_name: "泗阳星光装卸有限公司", region: "镇江",
  mobile: "", filing_status: "pending", filing_date: "", remarks: ""
});

Page({
  data: {
    form: emptyForm(), editingId: null, saving: false,
    genderOptions, genderIndex: 0, regionOptions, regionIndex: 0, statusOptions, statusIndex: 0
  },

  onLoad(options) {
    const id = Number(options.id || 0);
    if (id) {
      wx.setNavigationBarTitle({ title: "修改备案" });
      this.setData({ editingId: id });
      this.loadDetail(id);
    }
  },
  inputField(e) { this.setData({ [`form.${e.currentTarget.dataset.field}`]: e.detail.value }); },
  inputIdCard(e) {
    const idCard = e.detail.value.toUpperCase();
    let age = "";
    if (/^\d{17}[\dXx]$/.test(idCard)) {
      const birthDate = new Date(`${idCard.slice(6, 10)}-${idCard.slice(10, 12)}-${idCard.slice(12, 14)}T00:00:00`);
      if (!Number.isNaN(birthDate.getTime()) && birthDate.getFullYear() === Number(idCard.slice(6, 10)) && birthDate.getMonth() + 1 === Number(idCard.slice(10, 12)) && birthDate.getDate() === Number(idCard.slice(12, 14))) {
        const now = new Date();
        age = now.getFullYear() - birthDate.getFullYear();
        if (now.getMonth() < birthDate.getMonth() || (now.getMonth() === birthDate.getMonth() && now.getDate() < birthDate.getDate())) age -= 1;
      }
    }
    this.setData({ "form.id_card": idCard, "form.age": age });
  },
  changeGender(e) {
    const index = Number(e.detail.value);
    this.setData({ genderIndex: index, "form.gender": genderOptions[index] });
  },
  changeRegion(e) {
    const index = Number(e.detail.value);
    this.setData({ regionIndex: index, "form.region": regionOptions[index] });
  },
  changeStatus(e) {
    const index = Number(e.detail.value);
    const status = statusOptions[index].value;
    const changes = { statusIndex: index, "form.filing_status": status };
    if (status !== "filed") changes["form.filing_date"] = "";
    this.setData(changes);
  },
  changeDate(e) { this.setData({ "form.filing_date": e.detail.value }); },
  goBack() { wx.navigateBack(); },

  async loadDetail(id) {
    try {
      wx.showLoading({ title: "正在加载" });
      const record = await policeFilingApi.get(id);
      this.setData({
        form: {
          ...emptyForm(), ...record,
          company_name: "泗阳星光装卸有限公司",
          region: regionOptions.includes(record.region) ? record.region : "镇江",
          filing_date: record.filing_date || ""
        },
        genderIndex: Math.max(0, genderOptions.indexOf(record.gender)),
        regionIndex: Math.max(0, regionOptions.indexOf(record.region)),
        statusIndex: Math.max(0, statusOptions.findIndex(item => item.value === record.filing_status))
      });
    } catch (error) { wx.showToast({ title: error.message, icon: "none" }); }
    finally { wx.hideLoading(); }
  },

  async submit() {
    if (this.data.saving) return;
    const form = { ...this.data.form };
    Object.keys(form).forEach(key => { if (typeof form[key] === "string") form[key] = form[key].trim(); });
    if (!form.person_name || !form.id_card || !form.company_name || !form.region || !form.mobile) {
      wx.showToast({ title: "请填写全部必填信息", icon: "none" }); return;
    }
    if (form.person_name.length < 2) { wx.showToast({ title: "人员姓名至少填写2个字", icon: "none" }); return; }
    if (!/^\d{17}[\dXx]$/.test(form.id_card)) { wx.showToast({ title: "请输入正确的18位身份证号", icon: "none" }); return; }
    if (!/^[0-9+\-\s]{7,20}$/.test(form.mobile)) { wx.showToast({ title: "请输入正确的联系电话", icon: "none" }); return; }
    if (form.filing_status === "filed" && !form.filing_date) { wx.showToast({ title: "请选择备案日期", icon: "none" }); return; }
    delete form.age;
    delete form.id;
    delete form.created_at;
    if (form.filing_status !== "filed") delete form.filing_date;
    this.setData({ saving: true });
    try {
      wx.showLoading({ title: "正在保存", mask: true });
      await policeFilingApi.save(this.data.editingId, form);
      wx.showToast({ title: "保存成功", icon: "success" });
      setTimeout(() => wx.navigateBack(), 500);
    } catch (error) { wx.showToast({ title: error.message, icon: "none" }); }
    finally { wx.hideLoading(); this.setData({ saving: false }); }
  }
});
