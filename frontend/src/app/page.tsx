import { getHealth } from "@/lib/api";

export default async function HomePage() {
  const health = await getHealth();

  return (
    <main>
      <p className="eyebrow">Bond Insight</p>
      <h1>채권을 숫자 너머로 이해하세요.</h1>
      <p className="description">
        시장금리부터 개별 채권의 수익률, 듀레이션, 신용 스프레드까지 한 흐름에서
        탐색하고 비교하는 채권 분석 서비스입니다.
      </p>

      <section className="status-card" aria-labelledby="backend-status-title">
        <p className="status-label" id="backend-status-title">Backend 연결 상태</p>
        <p className="status-value" data-connected={health.connected}>
          {health.connected ? "정상 연결됨" : "Backend를 실행하면 연결 상태를 확인할 수 있습니다."}
        </p>
      </section>
    </main>
  );
}
