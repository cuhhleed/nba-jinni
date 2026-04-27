import type { Standing } from "../../types/teams";

type Props = {
  standing: Standing | null;
};

export default function TeamStandingWidget({ standing }: Props) {
  return (
    <div className="team-standing-container p-2 sm:p-3 lg:p-4 mx-6 rounded-lg grid grid-cols-2 hover:bg-amber-400">
      <h3 className="text-center text-[10px] sm:text-xl lg:text-2xl font-brand text-gray-900 col-span-2">
        {standing?.season} Standing
      </h3>
      <div className="col-span-1 sm:m-2 lg:m-4 m-3">
        <h3 className="text-[10px] sm:text-xl lg:text-2xl text-center text-gray-900 font-brand">
          Record
        </h3>
        <div className="border rounded-xl text-center bg-white text-[10px] text-amber-400 sm:text-2xl lg:text-3xl font-brand px-2 sm:px-3 lg:px-3 py-2 w-fit mx-auto">
          {standing?.wins}-{standing?.losses}
        </div>
      </div>
      <div className="col-span-1 sm:m-2 lg:m-4 m-3">
        <h3 className="text-[10px] sm:text-2xl lg:text-2xl text-center text-gray-900 font-brand">
          Rank
        </h3>
        <div className="border rounded-xl text-center bg-white text-[10px] sm:text-2xl lg:text-3xl text-amber-400 font-brand px-2 sm:px-3 lg:px-3 py-2 w-fit mx-auto">
          #{standing?.conference_rank}
        </div>
        <h4 className="text-[10px] sm:text-2xl lg:text-2xl text-center text-gray-900 font-brand">
          {standing?.conference}
        </h4>
      </div>
      <div className="col-span-1 sm:m-2 lg:m-4 m-3">
        <h3 className="text-[10px] sm:text-2xl lg:text-2xl text-center text-gray-900 font-brand">
          L10
        </h3>
        <div className="border rounded-xl text-center bg-white text-[10px] sm:text-2xl lg:text-3xl text-amber-400 font-brand px-2 sm:px-3 lg:px-3 py-2 w-fit mx-auto">
          {standing?.win_L10}-{standing?.loss_L10}
        </div>
      </div>
      <div className="col-span-1 sm:m-2 lg:m-4 m-3">
        <h3 className="text-[10px] sm:text-2xl lg:text-2xl text-center text-gray-900 font-brand">
          GB
        </h3>
        <div className="border rounded-xl text-center bg-white text-[10px] sm:text-2xl lg:text-3xl text-amber-400 font-brand px-2 sm:px-3 lg:px-3 py-2 w-fit mx-auto">
          {standing?.games_behind.toFixed(1)}
        </div>
      </div>
    </div>
  );
}
