import BondBridgeDashboard from "@/app/bond-bridge-dashboard";
import { getBondDashboardData } from "@/lib/bond-data";

export default async function HomePage() {
  const data = await getBondDashboardData();

  return <BondBridgeDashboard data={data} />;
}
