import React, { useState, useEffect } from "react";
import axios from "axios";

class Home extends React.Component{

    render(){
        return (
            <div>
                <h1>Meta Reinforcement Learning for Data Augmentation</h1>
                <h3>Choose your dataset</h3>
                <form action="/user_input" method="POST" encType="multipart/form-data">
                    <label htmlFor="dataset_upload">You can upload your dataset folder here:</label>
                    <input type="file" id='dataset_upload' name="dataset_upload" className="upload" /><br></br>

                    Or you can select a dataset from our database: <br/>
                    <input type="radio" id="dataset1"
                        name="dataset_selection" value="MNIST" />
                    <label htmlFor="dataset1">MNIST dataset</label><br/>

                    <input type="radio" id="dataset2"
                        name="dataset_selection" value="KMNIST" />
                    <label htmlFor="dataset2">KMNIST dataset</label><br />

                    <input type="radio" id="dataset3"
                        name="dataset_selection" value="FashionMNIST" />
                    <label htmlFor="dataset3">FashionMNIST dataset</label><br />

                    <input type="radio" id="dataset4"
                    name="dataset_selection" value="CIFAR10" />
                    <label htmlFor="dataset4">CIFAR10 dataset</label><br />

                    <input type="radio" id="dataset5"
                    name="dataset_selection" value="CIFAR100" />
                    <label htmlFor="dataset5">CIFAR100 dataset</label><br />

                    <input type="radio" id="dataset6"
                    name="dataset_selection" value="Other" />
                    <label htmlFor="dataset6">Other dataset DIFFERENT</label><br /><br /> 

                    <input type="submit"></input>
                </form>
            </div>
            
        );
    }
}

export default Home;