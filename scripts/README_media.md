# Kho ảnh thực tế & catalog BanlaTravel.vn

| File | Vai trò |
|---|---|
| `build_properties.py` → `properties.json` | Danh sách 86 sản phẩm (4 lô, 16 khu vực), slug, từ khóa xác minh tên cơ sở |
| `ota_media_pipeline.py` | Tìm ảnh (website chính thức / báo chí / blog review, loại OTA & stock), quality gate, WebP 1280px q82 → `frontend/assets/places/{region}/{slug}-0N.webp` |
| `checkpoint.json` | Tiến độ: lưu sau **mỗi** cơ sở; chạy lại sẽ tự bỏ qua cơ sở đã xong |
| `export_catalog.py` | Xuất `frontend/catalog.json`, kiểm định với `catalog.schema.json`, giới hạn dung lượng, viết `media_report.md` |
| `../.github/workflows/unpack-media.yml` | Giải nén gói ảnh base64 (`scripts/media-bundles/*.b64`) vào repo khi được đẩy lên |

```bash
pip install -r scripts/requirements-media.txt
python scripts/ota_media_pipeline.py              # chạy/tiếp tục cả 4 lô
python scripts/ota_media_pipeline.py --batch 3    # một lô
python scripts/ota_media_pipeline.py --reject ID:N   # loại ảnh N sau khi rà mắt rồi tìm bù
python scripts/ota_media_pipeline.py --drop ID:N     # loại ảnh N, không tìm bù
python scripts/ota_media_pipeline.py --hero ID:N     # đặt ảnh N làm ảnh đại diện (-01)
python scripts/export_catalog.py                  # xuất + kiểm định catalog (exit 1 nếu lỗi)
```

Quality gate: rộng ≥ 900px, tỷ lệ 1.3–1.9, loại ảnh mờ (Laplacian), ảnh trùng (dHash), viền/letterbox,
từ khóa render/phối cảnh/logo/bản đồ, mọi ảnh từ OTA/stock/Pinterest/YouTube; trang nguồn phải nêu đúng tên cơ sở.
Ảnh WebP ≤ 120 KB (tự hạ quality, khử nhiễu nhẹ với ảnh quá chi tiết). Mỗi ảnh có `source_url`, `source_page`, `credit`, `license_note`.
