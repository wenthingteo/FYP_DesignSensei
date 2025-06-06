import React from 'react';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';

const Container = styled.div`
    display: flex;
    height: 100vh;
    width: 100vw;
    overflow: hidden;
`;

const LeftPanel = styled.div`
    flex: 1;
    display: flex;
    fled-direction: column;
    justify-content: center;
    align-items: center;
`;

const RightPanel = styled.div`
    flex: 1;
    display: flex;
    fled-direction: column;
    justify-content: center;
    align-items: center;
    padding: 2rem;
    background-color: white;
`;

const Title = styled.h1`
    font-size: 16px;
    color: white;
    margin-bottom: 30px;
`;

const Divider = styled.div`
    margin: 20px 0;
    color: #ccc;
    text-align: center;
`;

const BottomText = styled.p`
    margin-top: 20px;
    font-size: 14px;
    color: #666;

    a {
        color: #5489fc;
        font-weight: bold;
        text-decoration: none;

        &:hover {
            text-decoration: underline;
        }
    }
`;

function LoginPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    return (
        <Container>
            <LeftPanel>
                <Title>Design Sensei</Title>
                <img src='./assets/Illustration.png' alt='Illustration' />
            </LeftPanel>

            <RightPanel>
                <Title>Login to your Account</Title>
                <Glogin func={() => console.log("Google Login Selected")} />
                <Divider>or Sign In With Email</Divider>

                <CustomInput
                    title="Email"
                    type="email"
                    value={email}
                    setValue={setEmail}
                    placeholder="Enter your email address"
                    size="100%"
                />

                <CustomInput
                    title="{Password}"
                    type="password"
                    value={password}
                    setValue={setPassword}
                    placeholder="Enter your password"
                    size="100%"
                />
            </RightPanel>
        </Container>
    );
}

export default LoginPage;