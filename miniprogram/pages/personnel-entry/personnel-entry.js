const { personnelApi } = require("../../api/index");

const positions = ["经理", "安全员", "会计", "带班长", "一班班组长", "二班班组长", "装卸工"];
const employmentStatuses = ["在职", "离职"];
const genders = ["男", "女"];
const educations = ["小学", "初中", "高中", "中专", "大专", "本科", "硕士及以上"];
const politicalStatuses = ["群众", "共青团员", "中共党员", "其他"];
const chronicDiseases = ["否", "高血压", "糖尿病"];
const insuranceTypes = ["大港+工伤险", "大港+雇主责任险"];

function today() {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${now.getFullYear()}-${month}-${day}`;
}

const emptyForm = () => ({
  staff_no: "", unit_name: "泗阳队", department_name: "泗阳劳务", position: "装卸工",
  employment_status: "在职", person_name: "", gender: "男", id_card: "", birth_date: "", age: "",
  nationality: "汉族", education: "小学", chronic_disease: "否", smokes: false,
  drinks_alcohol: false, native_place: "", political_status: "群众", joined_party_at: "",
  served_in_military: false, military_service_time: "", port_entry_date: today(), mobile: "",
  home_address: "", emergency_contact: "", emergency_mobile: "", insurance_type: "大港+工伤险",
  accident_insurance_limit: "150+"
});

function deriveIdentity(idCard) {
  if (!/^\d{17}[\dXx]$/.test(idCard)) return { birth_date: "", age: "" };
  const birth = `${idCard.slice(6, 10)}-${idCard.slice(10, 12)}-${idCard.slice(12, 14)}`;
  const birthDate = new Date(`${birth}T00:00:00`);
  if (Number.isNaN(birthDate.getTime()) || birthDate.getFullYear() !== Number(idCard.slice(6, 10)) || birthDate.getMonth() + 1 !== Number(idCard.slice(10, 12)) || birthDate.getDate() !== Number(idCard.slice(12, 14))) return { birth_date: "", age: "" };
  const now = new Date();
  let age = now.getFullYear() - birthDate.getFullYear();
  if (now.getMonth() < birthDate.getMonth() || (now.getMonth() === birthDate.getMonth() && now.getDate() < birthDate.getDate())) age -= 1;
  return { birth_date: birth, age };
}

Page({
  data: {
    form: emptyForm(), editingId: null, importing: false, saving: false,
    positions, positionIndex: 6, employmentStatuses, employmentStatusIndex: 0,
    genders, genderIndex: 0, educations, educationIndex: 0,
    politicalStatuses, politicalStatusIndex: 0, chronicDiseases, chronicDiseaseIndex: 0,
    insuranceTypes, insuranceIndex: 0,
    yesNoOptions: ["否", "是"]
  },

  onLoad(options) {
    const id = Number(options.id || 0);
    if (id) {
      wx.setNavigationBarTitle({ title: "修改人员" });
      this.setData({ editingId: id });
      this.loadDetail(id);
    }
  },
  inputField(e) { this.setData({ [`form.${e.currentTarget.dataset.field}`]: e.detail.value }); },
  inputIdCard(e) {
    const idCard = e.detail.value.toUpperCase();
    const derived = deriveIdentity(idCard);
    this.setData({ "form.id_card": idCard, "form.birth_date": derived.birth_date, "form.age": derived.age });
  },
  changePosition(e) { const index = Number(e.detail.value); this.setData({ positionIndex: index, "form.position": positions[index] }); },
  changeEmploymentStatus(e) { const index = Number(e.detail.value); this.setData({ employmentStatusIndex: index, "form.employment_status": employmentStatuses[index] }); },
  changeGender(e) { const index = Number(e.detail.value); this.setData({ genderIndex: index, "form.gender": genders[index] }); },
  changeEducation(e) { const index = Number(e.detail.value); this.setData({ educationIndex: index, "form.education": educations[index] }); },
  changePoliticalStatus(e) {
    const index = Number(e.detail.value);
    const politicalStatus = politicalStatuses[index];
    const changes = { politicalStatusIndex: index, "form.political_status": politicalStatus };
    if (politicalStatus === "群众") changes["form.joined_party_at"] = "";
    this.setData(changes);
  },
  changeChronicDisease(e) {
    const index = Number(e.detail.value);
    this.setData({ chronicDiseaseIndex: index, "form.chronic_disease": chronicDiseases[index] });
  },
  changeInsurance(e) { const index = Number(e.detail.value); this.setData({ insuranceIndex: index, "form.insurance_type": insuranceTypes[index] }); },
  changeBoolean(e) { this.setData({ [`form.${e.currentTarget.dataset.field}`]: Number(e.detail.value) === 1 }); },
  changeDate(e) { this.setData({ [`form.${e.currentTarget.dataset.field}`]: e.detail.value }); },
  goBack() { wx.navigateBack(); },

  async loadDetail(id) {
    try {
      wx.showLoading({ title: "正在加载" });
      const record = await personnelApi.get(id);
      const education = record.education || "小学";
      const politicalStatus = record.political_status || "群众";
      const chronicDisease = record.chronic_disease || "否";
      this.setData({
        form: {
          ...emptyForm(), ...record, education, political_status: politicalStatus, chronic_disease: chronicDisease,
          joined_party_at: politicalStatus === "群众" ? "" : record.joined_party_at || "",
          port_entry_date: record.port_entry_date || today(), military_service_time: record.military_service_time || ""
        },
        positionIndex: Math.max(0, positions.indexOf(record.position)),
        employmentStatusIndex: Math.max(0, employmentStatuses.indexOf(record.employment_status)),
        genderIndex: Math.max(0, genders.indexOf(record.gender)),
        educationIndex: Math.max(0, educations.indexOf(education)),
        politicalStatusIndex: Math.max(0, politicalStatuses.indexOf(politicalStatus)),
        chronicDiseaseIndex: Math.max(0, chronicDiseases.indexOf(chronicDisease)),
        insuranceIndex: Math.max(0, insuranceTypes.indexOf(record.insurance_type))
      });
    } catch (error) { wx.showToast({ title: error.message, icon: "none" }); }
    finally { wx.hideLoading(); }
  },

  chooseExcel() {
    wx.chooseMessageFile({ count: 1, type: "file", extension: ["xlsx"], success: result => this.uploadExcel(result.tempFiles[0].path) });
  },
  async uploadExcel(filePath) {
    this.setData({ importing: true });
    wx.showLoading({ title: "正在导入", mask: true });
    try {
      const result = await personnelApi.importExcel(filePath);
      const details = (result.errors || []).slice(0, 5).join("\n");
      wx.showModal({
        title: "导入完成",
        content: `成功 ${result.success_count} 人，失败 ${result.failure_count} 人${details ? `\n${details}` : ""}`,
        showCancel: false,
        success: () => { if (result.success_count) wx.navigateBack(); }
      });
    } catch (error) {
      wx.showToast({ title: error.message || "导入失败", icon: "none" });
    } finally {
      wx.hideLoading();
      this.setData({ importing: false });
    }
  },
  async downloadTemplate() {
    wx.showLoading({ title: "下载模板" });
    try {
      const filePath = await personnelApi.downloadTemplate();
      wx.openDocument({ filePath, fileType: "xlsx", showMenu: true });
    } catch (error) {
      wx.showToast({ title: error.message || "模板下载失败", icon: "none" });
    } finally {
      wx.hideLoading();
    }
  },

  async submit() {
    if (this.data.saving) return;
    const form = { ...this.data.form };
    Object.keys(form).forEach(key => { if (typeof form[key] === "string") form[key] = form[key].trim(); });
    if (!form.position || !form.employment_status || !form.person_name || !form.gender || !form.id_card || !form.mobile || !form.insurance_type) {
      wx.showToast({ title: "请填写全部必填信息", icon: "none" }); return;
    }
    if (!form.birth_date) { wx.showToast({ title: "请输入正确的18位身份证号", icon: "none" }); return; }
    if (form.person_name.length < 2) { wx.showToast({ title: "姓名至少填写2个字", icon: "none" }); return; }
    if (!/^1[3-9]\d{9}$/.test(form.mobile)) { wx.showToast({ title: "请输入11位手机号码", icon: "none" }); return; }
    const payload = {
      position: form.position, employment_status: form.employment_status, person_name: form.person_name,
      gender: form.gender, id_card: form.id_card, nationality: form.nationality || "汉族",
      education: form.education || "小学", chronic_disease: form.chronic_disease || "否", smokes: form.smokes,
      drinks_alcohol: form.drinks_alcohol, native_place: form.native_place || null,
      political_status: form.political_status || "群众",
      joined_party_at: form.political_status === "群众" ? null : form.joined_party_at || null,
      served_in_military: form.served_in_military,
      military_service_time: form.served_in_military ? form.military_service_time || null : null,
      port_entry_date: form.port_entry_date || today(), mobile: form.mobile, home_address: form.home_address || null,
      emergency_contact: form.emergency_contact || null, emergency_mobile: form.emergency_mobile || null,
      insurance_type: form.insurance_type
    };
    this.setData({ saving: true });
    try {
      wx.showLoading({ title: "正在保存", mask: true });
      await personnelApi.save(this.data.editingId, payload);
      wx.showToast({ title: "保存成功", icon: "success" });
      setTimeout(() => wx.navigateBack(), 500);
    } catch (error) { wx.showToast({ title: error.message, icon: "none" }); }
    finally { wx.hideLoading(); this.setData({ saving: false }); }
  }
});
