from __future__ import annotations

import os
import zipfile
from datetime import datetime


def _xml_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def _w_p(text: str) -> str:
    # WordprocessingML paragraph with a single run.
    t = _xml_escape(text)
    return f"<w:p><w:r><w:t xml:space='preserve'>{t}</w:t></w:r></w:p>"


def build_docx(paragraphs: list[str], out_path: str) -> None:
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>
"""

    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""

    doc_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
</Relationships>
"""

    body = "\n".join(_w_p(p) for p in paragraphs)
    document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    {body}
    <w:sectPr/>
  </w:body>
</w:document>
"""

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/document.xml", document_xml)
        z.writestr("word/_rels/document.xml.rels", doc_rels)


def main() -> None:
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    out_path = os.path.join(root, "Pickup-App-Documentation.docx")

    paragraphs: list[str] = []
    paragraphs.append("Plan for Green Earth — Application Documentation")
    paragraphs.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    paragraphs.append("")

    paragraphs.append("What the application does (10 sentences):")
    paragraphs.extend(
        [
            "1) This application helps people schedule plastic pickup requests and track them from request to pickup completion.",
            "2) It has three roles: Customer, Vendor, and Admin, each with their own screens and permissions.",
            "3) Customers can register/login, request a pickup by giving address and pickup date, and view their pickup history.",
            "4) Vendors can verify the plastic weight (kg) for a customer using the customer’s registered email.",
            "5) When plastic is verified, the system awards Eco-Points based on the verified weight and a configured rate (Eco-Points per kg).",
            "6) Customers can view their Eco-Points balance and complete history of verified weigh-ins.",
            "7) Customers can redeem Eco-Points in the Garden Shop for rewards like saplings, seeds, compost, and medicinal plants (with images).",
            "8) Each redemption records the item, points spent, status, and delivery details so it can be tracked.",
            "9) Admins can see all customer redemptions, mark items To send, and set a delivery date that cannot be before today.",
            "10) Overall, the app turns plastic recycling into a reward system that encourages a greener environment while keeping pickups and deliveries organized.",
        ]
    )
    paragraphs.append("")

    paragraphs.append("Greener environment impact (5 sentences):")
    paragraphs.extend(
        [
            "1) This app encourages a greener environment by rewarding people for recycling plastic instead of throwing it away.",
            "2) By scheduling pickups and verifying collected plastic, it helps ensure more waste is properly collected and processed, reducing litter and pollution.",
            "3) The Eco-Points system motivates consistent recycling habits, which lowers the amount of plastic reaching streets, drains, and water bodies.",
            "4) Redeeming points for saplings and medicinal plants directly supports more greenery, better air quality, and local biodiversity.",
            "5) Overall, it connects daily waste management to visible environmental impact: less plastic waste plus more plants.",
        ]
    )

    build_docx(paragraphs, out_path)
    print(out_path)


if __name__ == "__main__":
    main()

