/**
 * DataClean API — JavaScript 示例
 *
 * 5分钟快速开始：去重 + 标准化 + 一键清洗
 */

const API_BASE = "https://your-api-domain.com/v1";
const API_KEY = "dk_live_your_api_key_here";

const headers = {
  "X-API-Key": API_KEY,
  "Content-Type": "application/json",
};

async function main() {
  // ==================== 1. 批量去重 ====================
  console.log("=== 批量去重 ===");
  const dedupRes = await fetch(`${API_BASE}/dedup`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      records: [
        { id: 1, name: "张三", email: "ZhangSan@Gmail.com", phone: "138-1234-5678" },
        { id: 2, name: "张三", email: "zhangsan@gmail.com", phone: "13812345678" },
        { id: 3, name: "李四", email: "lisi@163.com", phone: "13900000000" },
      ],
      match_fields: ["name", "email", "phone"],
      match_mode: "fuzzy",
      similarity_threshold: 0.85,
      standardize_before_match: true,
    }),
  });
  const dedupData = await dedupRes.json();
  console.log(`输入 ${dedupData.total_records} 条，去重后 ${dedupData.unique_count} 条`);
  console.log(`重复 ${dedupData.duplicate_count} 条，耗时 ${dedupData.processing_time_ms}ms\n`);

  // ==================== 2. 标准化 ====================
  console.log("=== 标准化 ===");
  const stdRes = await fetch(`${API_BASE}/standardize`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      records: [
        { phone: "+86 138-1234-5678", email: "  ZhangSan@Gmail.com  ", address: "北京市海淀区中关村大街1号" },
      ],
      fields: ["phone", "email", "address"],
    }),
  });
  const stdData = await stdRes.json();
  console.log("标准化后:", stdData.standardized_records[0], "\n");

  // ==================== 3. 一键综合清洗 ====================
  console.log("=== 一键综合清洗 ===");
  const cleanRes = await fetch(`${API_BASE}/clean`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      records: [
        { id: 1, name: "张三", email: "ZhangSan@Gmail.com", phone: "138-1234-5678", address: "北京市海淀区中关村大街1号" },
        { id: 2, name: "张三", email: "zhangsan@gmail.com", phone: "13812345678", address: "北京海淀区中关村大街1号" },
        { id: 3, name: "invalid", email: "bad@@email.com", phone: "13900000000", address: "上海市浦东新区" },
      ],
      pipeline: ["standardize", "validate", "dedup"],
      config: {
        standardize: { fields: ["phone", "email", "address"] },
        validate: { email_check: "format" },
        dedup: { match_fields: ["email", "phone"], mode: "fuzzy", threshold: 0.85 },
      },
    }),
  });
  const cleanData = await cleanRes.json();
  console.log(`输入 ${cleanData.summary.input_count} 条 → 最终 ${cleanData.summary.final_count} 条`);
  console.log(`质量评分: ${cleanData.quality_report.overall_score}/100`);
  console.log(`完整性: ${cleanData.quality_report.completeness}`);
  console.log(`唯一性: ${cleanData.quality_report.uniqueness}`);
  console.log(`有效性: ${cleanData.quality_report.validity}`);
}

main().catch(console.error);
