import PlayerPage from './PlayerPage';

export default async function Page({
  params,
}: {
  params: Promise<{ gameName: string; tagLine: string }>;
}) {
  const { gameName, tagLine } = await params;
  return (
    <PlayerPage
      gameName={decodeURIComponent(gameName)}
      tagLine={decodeURIComponent(tagLine)}
    />
  );
}
