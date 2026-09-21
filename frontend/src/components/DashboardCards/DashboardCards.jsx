import "./DashboardCards.css";

const DashboardCards = () => {

const data=[

{
title:"Students",

value:53,

color:"#4b4df5"
},

{
title:"Lessons",

value:12,

color:"#20bf6b"
},

{
title:"Feedback",

value:426,

color:"#ff6b6b"
},

{
title:"Engagement",

value:"82%",

color:"#f7b731"
}

];

return(

<div className="cards">

{data.map((card,index)=>(

<div
key={index}
className="card"
style={{
borderTop:`5px solid ${card.color}`
}}
>

<h4>{card.title}</h4>

<h2>{card.value}</h2>

</div>

))}

</div>

)

}

export default DashboardCards;