import { useNavigate } from "react-router-dom";

type Props = {
  title: string;
  to: string;
};

export const ModuleCard = ({ title, to }: Props) => {
  const navigate = useNavigate();

  const handleClick = () => {
    navigate(to);
  };

  return (
    <div
      className="module-card cursor-pointer"
      onClick={handleClick}
    >
      <h2>{title}</h2>
    </div>
  );
};
