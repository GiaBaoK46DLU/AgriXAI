import '../core/app_colors.dart';
import '../models/models.dart';

/// Phần còn lại của bản thiết kế **AgriXAI Farmer v4** chưa/không nối API
/// thật: danh mục 10 bệnh dùng làm dữ liệu giả cho `flutter test`
/// (`test/app_smoke_test.dart` dựng JSON `GET /diseases` từ [diseases]), và
/// các bảng tra màu/nhãn theo [Severity]/[PathogenType] dùng chung cho cả dữ
/// liệu thật lẫn giả. Lô đất, lịch sử chẩn đoán và thời tiết đã nối API thật
/// nên không còn dữ liệu mẫu ở đây nữa — xem `Plot.fromJson`,
/// `DiagnosisEntry.fromJson`, `WeatherSnapshot.fromJson`.
class DemoData {
  const DemoData._();

  // ── Mức độ ─────────────────────────────────────────────────────────────
  static final Map<Severity, SeverityStyle> severity =
      <Severity, SeverityStyle>{
    Severity.none: SeverityStyle(
      name: 'Khoẻ mạnh',
      bg: AgriColors.primaryLightA(.2),
      fg: AgriColors.primary,
      dot: AgriColors.primary,
      leafA: AgriColors.olive,
      leafB: AgriColors.primary,
      iconBg: AgriColors.primaryLightA(.2),
    ),
    Severity.mild: SeverityStyle(
      name: 'Nhẹ',
      bg: AgriColors.oliveA(.18),
      fg: AgriColors.oliveInk,
      dot: AgriColors.oliveInk,
      leafA: AgriColors.oliveInk,
      leafB: AgriColors.primary,
      iconBg: AgriColors.oliveA(.18),
    ),
    Severity.moderate: SeverityStyle(
      name: 'Trung bình',
      bg: AgriColors.accentA(.2),
      fg: AgriColors.accentInk,
      dot: AgriColors.accentInk,
      leafA: AgriColors.accentInk,
      leafB: AgriColors.oliveInk,
      iconBg: AgriColors.accentA(.2),
    ),
    Severity.severe: SeverityStyle(
      name: 'Nặng',
      bg: AgriColors.severeBg,
      fg: AgriColors.severeFg,
      dot: AgriColors.severeDot,
      leafA: AgriColors.accent,
      leafB: AgriColors.severeDot,
      iconBg: AgriColors.severeDotA(.22),
    ),
  };

  static SeverityStyle sev(Severity s) => severity[s] ?? severity[Severity.mild]!;

  // ── Nhóm tác nhân ──────────────────────────────────────────────────────
  static final Map<PathogenType, PathogenTypeStyle> typeTag =
      <PathogenType, PathogenTypeStyle>{
    PathogenType.fungus: PathogenTypeStyle(
      label: 'Nấm',
      bg: AgriColors.oliveA(.16),
      fg: AgriColors.oliveInk,
      dot: AgriColors.oliveInk,
    ),
    PathogenType.bacteria: PathogenTypeStyle(
      label: 'Vi khuẩn',
      bg: AgriColors.primaryLightA(.18),
      fg: AgriColors.primary,
      dot: AgriColors.primary,
    ),
    PathogenType.virus: PathogenTypeStyle(
      label: 'Virus',
      bg: AgriColors.accentA(.18),
      fg: AgriColors.accentInk,
      dot: AgriColors.accentInk,
    ),
    PathogenType.pest: PathogenTypeStyle(
      label: 'Nhện hại',
      bg: AgriColors.whiteA(.78),
      fg: AgriColors.inkA(.85),
      dot: AgriColors.inkSoftA(.7),
    ),
    PathogenType.healthy: PathogenTypeStyle(
      label: 'Khoẻ',
      bg: AgriColors.primaryLightA(.2),
      fg: AgriColors.primary,
      dot: AgriColors.primary,
    ),
  };

  static PathogenTypeStyle tag(PathogenType t) =>
      typeTag[t] ?? typeTag[PathogenType.fungus]!;

  // ── Mười lớp bệnh ──────────────────────────────────────────────────────
  static const List<Disease> diseases = <Disease>[
    Disease(
      key: 'late_blight',
      name: 'Mốc sương muộn',
      en: 'Late blight',
      type: PathogenType.fungus,
      pathogen: 'Nấm trứng Phytophthora infestans',
      cue: 'Mảng cháy lớn màu nâu xám loang lổ, viền nhợt như bị nước sôi dội qua.',
      symptoms:
          'Mảng bệnh lớn, không có hình dạng rõ ràng, màu xanh xám rồi chuyển nâu đen, lan rất nhanh. Mặt dưới lá có lớp mốc trắng mịn khi trời ẩm. Thân và quả cũng bị thối nâu cứng.',
      conditions:
          'Trời mát ẩm, nhiệt độ 15–22°C kèm mưa phùn hoặc sương mù kéo dài — điều kiện rất phổ biến ở Đà Lạt.',
      treatments: <String>[
        'Bệnh lan rất nhanh — xử lý ngay trong vòng 24 giờ khi phát hiện.',
        'Nhổ bỏ và tiêu huỷ toàn bộ cây bệnh nặng, đưa ra khỏi ruộng.',
        'Phun thuốc đặc hiệu, luân phiên hoạt chất giữa các lần phun.',
        'Phun phòng cho các cây xung quanh ngay cả khi chưa có triệu chứng.',
      ],
      products: <ProductLink>[
        ProductLink(
          name: 'Metalaxyl + Mancozeb',
          group: 'Trừ nấm lưu dẫn kết hợp tiếp xúc',
        ),
        ProductLink(
          name: 'Cymoxanil',
          group: 'Trừ nấm lưu dẫn — đặc hiệu nấm trứng',
        ),
        ProductLink(name: 'Dimethomorph', group: 'Trừ nấm lưu dẫn'),
      ],
      prevention: <String>[
        'Theo dõi dự báo thời tiết, phun phòng trước các đợt mưa ẩm kéo dài.',
        'Trồng giống có khả năng kháng bệnh.',
        'Tuyệt đối không trồng cà chua cạnh ruộng khoai tây.',
      ],
    ),
    Disease(
      key: 'early_blight',
      name: 'Đốm vòng (đốm nâu)',
      en: 'Early blight',
      type: PathogenType.fungus,
      pathogen: 'Nấm Alternaria solani',
      cue: 'Đốm nâu sẫm có vòng đồng tâm như hình bia bắn, xung quanh ngả vàng.',
      symptoms:
          'Đốm nâu sẫm với các vòng đồng tâm đặc trưng, đường kính tới 10 mm, xuất hiện ở lá gốc trước rồi lan dần lên. Mô quanh vết bệnh ngả vàng, lá khô và rụng từ dưới lên.',
      conditions:
          'Ẩm độ cao xen kẽ khô hạn, nhiệt độ 24–29°C; cây thiếu dinh dưỡng hoặc đang mang nhiều quả dễ nhiễm nặng.',
      treatments: <String>[
        'Cắt bỏ lá gốc bị bệnh, dọn sạch tàn dư trên mặt luống.',
        'Phun luân phiên các nhóm hoạt chất khác nhau để tránh kháng thuốc.',
        'Bón cân đối đạm – lân – kali, tránh để cây suy kiệt trong giai đoạn nuôi quả.',
      ],
      products: <ProductLink>[
        ProductLink(name: 'Mancozeb', group: 'Trừ nấm tiếp xúc phổ rộng'),
        ProductLink(name: 'Chlorothalonil', group: 'Trừ nấm tiếp xúc'),
        ProductLink(
          name: 'Azoxystrobin',
          group: 'Trừ nấm lưu dẫn nhóm strobilurin',
        ),
        ProductLink(
          name: 'Difenoconazole',
          group: 'Trừ nấm lưu dẫn nhóm triazole',
        ),
      ],
      prevention: <String>[
        'Phủ gốc bằng rơm hoặc màng phủ để hạn chế bào tử từ đất bắn lên lá.',
        'Luân canh, cày vùi tàn dư sau vụ.',
        'Tỉa bớt lá gốc để tán thông thoáng.',
      ],
    ),
    Disease(
      key: 'bacterial_spot',
      name: 'Đốm lá vi khuẩn',
      en: 'Bacterial spot',
      type: PathogenType.bacteria,
      pathogen: 'Vi khuẩn Xanthomonas spp.',
      cue: 'Nhiều đốm nhỏ sũng nước, sau chuyển nâu đen và có quầng vàng bao quanh.',
      symptoms:
          'Trên lá xuất hiện các đốm nhỏ đường kính 1–3 mm, ban đầu sũng nước rồi chuyển nâu sẫm, thường có quầng vàng. Đốm dày lên làm lá vàng và rụng sớm. Trên quả có đốm sần sùi màu nâu.',
      conditions:
          'Ẩm độ cao, mưa nhiều, nhiệt độ 24–30°C; lây lan mạnh khi tưới phun mưa hoặc thao tác trên ruộng lúc lá còn ướt.',
      treatments: <String>[
        'Ngắt bỏ và tiêu huỷ lá bệnh, không vứt tại ruộng.',
        'Phun thuốc gốc đồng, có thể phối hợp thuốc trừ nấm tiếp xúc.',
        'Ngừng tưới phun mưa lên tán lá, chuyển sang tưới gốc hoặc nhỏ giọt.',
        'Không thao tác chăm sóc khi lá còn ướt để hạn chế lây lan.',
      ],
      products: <ProductLink>[
        ProductLink(
          name: 'Copper hydroxide',
          group: 'Thuốc gốc đồng — kháng khuẩn',
        ),
        ProductLink(
          name: 'Copper oxychloride',
          group: 'Thuốc gốc đồng — kháng khuẩn',
        ),
        ProductLink(name: 'Mancozeb', group: 'Phối hợp để tăng hiệu quả'),
      ],
      prevention: <String>[
        'Dùng hạt giống và cây con sạch bệnh.',
        'Luân canh với cây khác họ cà tối thiểu 2 năm.',
        'Trồng thưa hợp lý để tán lá thông thoáng, mau khô.',
      ],
    ),
    Disease(
      key: 'septoria_leaf_spot',
      name: 'Đốm lá Septoria',
      en: 'Septoria leaf spot',
      type: PathogenType.fungus,
      pathogen: 'Nấm Septoria lycopersici',
      cue: 'Rất nhiều đốm tròn nhỏ, tâm xám trắng viền nâu sẫm, phân bố dày đặc.',
      symptoms:
          'Đốm tròn nhỏ 1–3 mm, tâm màu xám trắng với viền nâu sẫm rõ nét, số lượng rất nhiều trên một lá. Xuất hiện ở lá gốc trước, làm lá vàng và rụng từ dưới lên.',
      conditions:
          'Ẩm ướt kéo dài, nhiệt độ 20–25°C; bào tử lây lan qua nước mưa và nước tưới bắn từ đất.',
      treatments: <String>[
        'Ngắt bỏ lá bệnh ngay khi mới xuất hiện ở tầng gốc.',
        'Phun luân phiên hoạt chất để tránh kháng thuốc.',
        'Chuyển sang tưới gốc, tránh nước bắn từ mặt đất lên lá.',
      ],
      products: <ProductLink>[
        ProductLink(name: 'Chlorothalonil', group: 'Trừ nấm tiếp xúc'),
        ProductLink(name: 'Mancozeb', group: 'Trừ nấm tiếp xúc phổ rộng'),
        ProductLink(name: 'Azoxystrobin', group: 'Trừ nấm lưu dẫn'),
      ],
      prevention: <String>[
        'Phủ gốc bằng rơm hoặc màng phủ nông nghiệp.',
        'Dọn sạch và tiêu huỷ tàn dư cây sau thu hoạch.',
        'Luân canh tối thiểu 2 năm với cây khác họ cà.',
      ],
    ),
    Disease(
      key: 'leaf_mold',
      name: 'Mốc lá',
      en: 'Leaf mold',
      type: PathogenType.fungus,
      pathogen: 'Nấm Passalora fulva',
      cue: 'Mảng vàng nhạt mờ ở mặt trên lá, mặt dưới phủ lớp mốc màu ô liu.',
      symptoms:
          'Mặt trên lá có mảng vàng nhạt ranh giới không rõ; mặt dưới đúng vị trí đó phủ lớp nấm mượt màu ô liu đến nâu. Lá bệnh khô, quăn lại và rụng. Phổ biến trong nhà kính, nhà lưới.',
      conditions:
          'Ẩm độ trên 85% và thông gió kém — đặc biệt hay gặp trong nhà kính, nhà màng.',
      treatments: <String>[
        'Tăng thông gió, giảm ẩm độ trong nhà kính — đây là biện pháp quan trọng nhất.',
        'Ngắt bỏ lá bệnh ở tầng dưới.',
        'Chỉ phun thuốc khi bệnh đã xuất hiện, không phun phòng tràn lan.',
      ],
      products: <ProductLink>[
        ProductLink(name: 'Chlorothalonil', group: 'Trừ nấm tiếp xúc'),
        ProductLink(name: 'Mancozeb', group: 'Trừ nấm tiếp xúc phổ rộng'),
        ProductLink(name: 'Difenoconazole', group: 'Trừ nấm lưu dẫn'),
      ],
      prevention: <String>[
        'Trồng mật độ vừa phải, tỉa lá tạo độ thông thoáng.',
        'Tưới vào buổi sáng để lá kịp khô trước đêm.',
        'Vệ sinh, khử trùng nhà kính giữa các vụ.',
      ],
    ),
    Disease(
      key: 'target_spot',
      name: 'Đốm mắt cua',
      en: 'Target spot',
      type: PathogenType.fungus,
      pathogen: 'Nấm Corynespora cassiicola',
      cue: 'Đốm nâu có vòng tròn đồng tâm mờ, tâm vết bệnh sáng màu và khô nứt.',
      symptoms:
          'Đốm nâu nhạt đến nâu sẫm với vòng đồng tâm mờ, tâm vết bệnh thường sáng màu, khô và có thể nứt rách. Xuất hiện trên cả lá, thân và quả; dễ nhầm với đốm vòng.',
      conditions:
          'Ẩm độ cao và nhiệt độ ấm 20–30°C, tán lá rậm rạp ít thông thoáng.',
      treatments: <String>[
        'Loại bỏ lá bệnh, tỉa thưa tán lá cho thông thoáng.',
        'Phun thuốc trừ nấm, luân phiên nhóm hoạt chất giữa các lần phun.',
        'Tránh tưới phun mưa vào chiều tối.',
      ],
      products: <ProductLink>[
        ProductLink(name: 'Azoxystrobin', group: 'Trừ nấm lưu dẫn'),
        ProductLink(name: 'Difenoconazole', group: 'Trừ nấm lưu dẫn'),
        ProductLink(name: 'Mancozeb', group: 'Trừ nấm tiếp xúc phổ rộng'),
      ],
      prevention: <String>[
        'Trồng thưa, làm giàn giúp tán lá khô nhanh sau mưa.',
        'Dọn sạch tàn dư, luân canh cây trồng.',
        'Tránh tưới phun mưa vào chiều tối.',
      ],
    ),
    Disease(
      key: 'spider_mites',
      name: 'Nhện đỏ hai chấm',
      en: 'Two-spotted spider mite',
      type: PathogenType.pest,
      pathogen:
          'Nhện hại Tetranychus urticae — không phải nấm hay vi khuẩn',
      cue: 'Vô số chấm li ti màu vàng bạc rải đều trên phiến lá, lá mất màu như bị phủ bụi.',
      symptoms:
          'Lá lấm tấm chấm vàng nhạt li ti do nhện chích hút, dần bạc màu và khô giòn. Khi mật độ cao thấy tơ mỏng ở mặt dưới lá và kẽ lá.',
      conditions:
          'Thời tiết nóng khô, ít mưa; bùng phát mạnh khi lạm dụng thuốc trừ sâu phổ rộng làm chết thiên địch.',
      treatments: <String>[
        'Phun mạnh nước lên mặt dưới lá để rửa trôi nhện — hiệu quả khi mật độ còn thấp.',
        'Dùng thuốc trừ nhện chuyên biệt, không dùng thuốc trừ nấm.',
        'Luân phiên hoạt chất vì nhện đỏ kháng thuốc rất nhanh.',
      ],
      products: <ProductLink>[
        ProductLink(name: 'Abamectin', group: 'Trừ nhện — nguồn gốc sinh học'),
        ProductLink(name: 'Spiromesifen', group: 'Trừ nhện, diệt cả trứng'),
        ProductLink(
          name: 'Dầu khoáng',
          group: 'Bịt lỗ thở — an toàn cho thiên địch',
        ),
      ],
      prevention: <String>[
        'Giữ ẩm độ vườn hợp lý, tránh để khô hạn kéo dài.',
        'Hạn chế thuốc trừ sâu phổ rộng để bảo vệ thiên địch.',
        'Kiểm tra mặt dưới lá định kỳ để phát hiện sớm.',
      ],
    ),
    Disease(
      key: 'yellow_leaf_curl_virus',
      name: 'Virus xoăn vàng lá',
      en: 'Tomato Yellow Leaf Curl Virus',
      type: PathogenType.virus,
      pathogen: 'Virus TYLCV, lan truyền qua bọ phấn trắng',
      cue: 'Lá nhỏ lại, mép lá cuốn ngược lên trên và vàng rõ ở phần rìa.',
      symptoms:
          'Lá non nhỏ hẹp bất thường, mép lá cuốn ngược lên trên và vàng từ rìa vào trong. Cây lùn, đốt ngắn, rụng hoa, hầu như không đậu quả. Nhiễm sớm có thể mất trắng.',
      conditions: 'Mật độ bọ phấn trắng (Bemisia tabaci) cao; thời tiết nóng khô.',
      treatments: <String>[
        'Không có thuốc chữa virus — phải nhổ bỏ và tiêu huỷ cây bệnh ngay để cắt nguồn lây.',
        'Tập trung diệt môi giới truyền bệnh là bọ phấn trắng.',
        'Đặt bẫy dính màu vàng để theo dõi và giảm mật độ bọ phấn.',
      ],
      products: <ProductLink>[
        ProductLink(
          name: 'Pymetrozine',
          group: 'Trừ bọ phấn — chặn môi giới truyền virus',
          note: 'Trị bọ phấn trắng — môi giới truyền bệnh, không phải trị virus',
        ),
        ProductLink(
          name: 'Dinotefuran',
          group: 'Trừ bọ phấn lưu dẫn',
          note: 'Trị bọ phấn trắng — môi giới truyền bệnh, không phải trị virus',
        ),
        ProductLink(
          name: 'Dầu khoáng',
          group: 'Xua và bịt lỗ thở bọ phấn',
          note: 'Xua và bịt lỗ thở bọ phấn, không phải trị virus',
        ),
      ],
      prevention: <String>[
        'Trồng giống kháng TYLCV — biện pháp hiệu quả nhất.',
        'Che lưới chắn côn trùng cho vườn ươm và nhà màng.',
        'Nhổ sạch cỏ dại quanh ruộng vì đó là nơi trú của bọ phấn.',
      ],
    ),
    Disease(
      key: 'mosaic_virus',
      name: 'Virus khảm',
      en: 'Tomato mosaic virus',
      type: PathogenType.virus,
      pathogen: 'Virus ToMV/TMV, lan truyền qua tiếp xúc cơ học',
      cue: 'Phiến lá loang lổ xanh đậm xen xanh nhạt như bức tranh khảm, bề mặt gồ ghề.',
      symptoms:
          'Phiến lá loang lổ các mảng xanh đậm xen xanh nhạt hoặc vàng, bề mặt lá nhăn gồ ghề, lá có thể hẹp lại hình sợi. Cây sinh trưởng chậm, quả nhỏ và chín không đều.',
      conditions:
          'Lây qua tay người, dụng cụ, quần áo khi chăm sóc; virus tồn tại rất lâu trong tàn dư và hạt giống.',
      treatments: <String>[
        'Không có thuốc chữa virus — nhổ bỏ và tiêu huỷ cây bệnh.',
        'Rửa tay và khử trùng dụng cụ bằng cồn hoặc dung dịch javel sau khi chạm cây bệnh.',
        'Không hút thuốc lá khi làm việc trong ruộng cà chua.',
      ],
      products: <ProductLink>[],
      noProductText:
          'Không có thuốc trị virus khảm. Chỉ xử lý bằng cách nhổ bỏ cây bệnh và khử trùng tay, dụng cụ — mua thuốc trong trường hợp này là vô ích.',
      prevention: <String>[
        'Dùng hạt giống sạch bệnh, đã qua xử lý.',
        'Khử trùng dụng cụ trước và sau mỗi lần sử dụng.',
        'Thao tác với cây khoẻ trước, cây nghi bệnh sau cùng.',
      ],
    ),
    Disease(
      key: 'healthy',
      name: 'Lá khoẻ mạnh',
      en: 'Healthy',
      type: PathogenType.healthy,
      pathogen: 'Không có tác nhân gây bệnh',
      cue: 'Phiến lá xanh đều, không có đốm, không biến dạng.',
      symptoms:
          'Lá xanh đều, phiến lá phẳng, không có đốm bệnh, không biến màu hay biến dạng.',
      conditions: 'Không áp dụng.',
      treatments: <String>[
        'Không cần xử lý. Tiếp tục duy trì chế độ chăm sóc hiện tại.',
        'Kiểm tra vườn định kỳ 3–5 ngày một lần để phát hiện sớm bất thường.',
      ],
      products: <ProductLink>[],
      noProductText:
          'Lá đang khoẻ — không cần dùng thuốc. Giữ nguyên chế độ chăm sóc và kiểm tra vườn định kỳ.',
      prevention: <String>[
        'Bón phân cân đối, tưới nước đều đặn.',
        'Giữ vườn thông thoáng, sạch cỏ dại.',
      ],
    ),
  ];

  static Disease diseaseByKey(String key) => diseases.firstWhere(
        (Disease d) => d.key == key,
        orElse: () => diseases.first,
      );

  /// '94%' → 0.94, dùng cho bề rộng thanh tiến trình.
  static double percentToFraction(String percent) {
    final double? value =
        double.tryParse(percent.replaceAll('%', '').trim());
    if (value == null) return 0;
    return (value / 100).clamp(0.0, 1.0);
  }
}
